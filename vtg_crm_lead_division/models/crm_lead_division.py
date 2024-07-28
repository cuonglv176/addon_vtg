# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import urllib3
import certifi
from datetime import date, datetime, timedelta


class CrmLeadDivisionDepartment(models.Model):
    _name = 'crm.lead.division.department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    lead_count = fields.Integer('Tổng Lead', compute='_compute_lead_count')
    detail_ids = fields.One2many('crm.lead.division.department.detail', 'division_id')
    total_percent = fields.Float(string='Tổng %', compute='_compute_total_percent')

    @api.depends('detail_ids.percent')
    def _compute_total_percent(self):
        for rec in self:
            total_percent = 0
            for detail_id in rec.detail_ids:
                total_percent += detail_id.percent
            rec.total_percent = total_percent * 100

    @api.onchange('total_percent')
    def onchange_total_percent(self):
        if self.total_percent > 1:
            raise UserError(_("Tỉ lệ % phải nhỏ hơn 100%"))

    def _compute_lead_count(self):
        for rec in self:
            lead_ids = self.env['crm.lead'].sudo().search(
                [('create_date', '>', datetime.today() - relativedelta(days=1)),
                 ('create_date', '<', datetime.today() + relativedelta(days=1))])
            old_lead_ids = self.env['crm.lead'].sudo().search(
                [('create_date', '<', datetime.today() - relativedelta(days=1)),
                 ('type', '=', 'lead'), ('type_lead', '!=', 'resale')])
            rec.lead_count = len(lead_ids) + len(old_lead_ids)

    @api.model
    def show_configuration(self):
        view = self.env.ref("vtg_crm_lead_division.vtg_crm_lead_division_department_form_view", False)
        if view:
            return {
                "name": _("Cấu hình tỉ lệ lấy lead"),
                "type": "ir.actions.act_window",
                "res_model": "crm.lead.division.department",
                "view_mode": "form",
                "view_id": view.id,
                "res_id": self.search([], limit=1).id,
                "target": "main",
            }


class CrmLeadDivisionDepartmentDetail(models.Model):
    _name = 'crm.lead.division.department.detail'
    _order = 'create_date desc'

    division_id = fields.Many2one('crm.lead.division.department', 'Cài đặt Tỉ lệ')
    department_id = fields.Many2one('hr.department', string='Phòng')
    percent = fields.Float(string='Tỉ lệ')
    lead_get = fields.Integer('Lead được lấy (Trong ngày)', compute='_compute_lead_get_count')
    lead_department_count = fields.Integer('Lead đã lấy (Trong ngày)', compute='_compute_lead_department_count')

    def _compute_lead_department_count(self):
        for rec in self:
            lead_ids = self.env['crm.lead'].sudo().search(
                [('date_open', '>', datetime.today() - relativedelta(days=1)),
                 ('date_open', '<', datetime.today() + relativedelta(days=1)),
                 ('department_id', '=', rec.department_id.id)])
            rec.lead_department_count = len(lead_ids)

    def _compute_lead_get_count(self):
        for rec in self:
            lead_ids = self.env['crm.lead'].sudo().search(
                [('create_date', '>', datetime.today() - relativedelta(days=1)),
                 ('create_date', '<', datetime.today() + relativedelta(days=1))])
            old_lead_ids = self.env['crm.lead'].sudo().search(
                [('create_date', '<', datetime.today() - relativedelta(days=1)),
                 ('type', '=', 'lead'), ('type_lead', '!=', 'resale')])
            lead_count = len(lead_ids) + len(old_lead_ids)
            rec.lead_get = round(lead_count * rec.percent)


class CrmLeadDivision(models.Model):
    _name = 'crm.lead.division'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    @api.model
    def _get_default_code(self):
        return self.env["ir.sequence"].next_by_code("crm.lead.division")

    name = fields.Char(string='Mã ', track_visibility='onchange')
    line_ids = fields.One2many('crm.lead.division.line', 'division_id', string='Chi tiết chia')
    team_id = fields.Many2one('crm.team', string="Nhóm bán hàng", required=True)
    date = fields.Date(string="Ngày", required=True, default=lambda d: date.today())
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Xác nhận'),
        ('cancel', 'Từ chối')
    ], string='Trạng thái', default='draft', track_visibility='onchange')
    total_lead = fields.Integer(string='Tổng lead đang có', compute="_compute_total_lead")
    department_id = fields.Many2one('hr.department', string='Phòng ban')

    @api.onchange('department_id')
    def onchange_department(self):
        if not self.department_id:
            employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)])
            self.department_id = employee_id.department_id

    def _compute_total_lead(self):
        for rec in self:
            division_department_id = self.env['crm.lead.division.department.detail'].sudo().search(
                [('department_id', '=', rec.department_id.id), ('division_id', '=', 1)])
            rec.total_lead = division_department_id.lead_get

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('crm.lead.division') or '/'
        kpi = super(CrmLeadDivision, self).create(vals)
        return kpi

    def action_confirm(self):
        self.state = 'confirmed'
        for line_id in self.line_ids:
            if line_id.qty_lead > 0:
                limit = line_id.qty_lead
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('type', '=', 'lead'), ('user_id', '=', False), ('team_id', '=', self.team_id.id)], limit=limit)
                for lead_id in lead_ids:
                    lead_id.write({
                        'user_id': line_id.user_id.id,
                        'team_id': self.team_id.id,
                        'type': 'opportunity',
                    })

    def action_cancel(self):
        self.state = 'cancel'

    @api.onchange('team_id')
    def onchange_members(self):
        self.line_ids.unlink()
        if self.team_id:
            for member_id in self.team_id.member_ids:
                vals = {
                    'user_id': member_id.id,
                    'qty_lead': 0,
                }
                self.update({'line_ids': [(0, 0, vals)]})


class CRMKpiMktLine(models.Model):
    _name = 'crm.lead.division.line'

    division_id = fields.Many2one('crm.lead.division', string='Division')
    user_id = fields.Many2one('res.users', string='Nhân viên', required=True)
    date = fields.Date(string="Ngày", required=True, default=lambda d: date.today())
    qty_lead = fields.Integer(string='Số lead nhận')
    ok = fields.Boolean('Hoạt động', default=True)
    lead_count = fields.Integer('Lead đã lấy', compute='_compute_lead_count')

    def _compute_lead_count(self):
        for rec in self:
            lead_ids = self.env['crm.lead'].sudo().search(
                [('date_open', '>', datetime.today() - relativedelta(days=1)),
                 ('date_open', '<', datetime.today() + relativedelta(days=1)),
                 ('user_id', '=', rec.user_id.id)])
            rec.lead_count = len(lead_ids)
