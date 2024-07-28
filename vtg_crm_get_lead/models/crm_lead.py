# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, date
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
import logging
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)


class CrmTeamMember(models.Model):
    _inherit = 'crm.team.member'

    max_lead = fields.Integer(string='Số lead mới được lấy trong ngày')


class LeadJOB(models.Model):
    _name = 'crm.lead.job'

    name = fields.Char('Tên nghề nghiệp')


class AccountMove(models.Model):
    _inherit = 'account.move'

    type_get_lead = fields.Selection(selection=[('new', 'Mới'),
                                                ('old', 'Cũ'),
                                                ('create', 'Tự tạo'),
                                                ],
                                     string='Loại lấy lead', compute="_get_type_get_lead", store=True)
    create_lead = fields.Datetime(string='Ngày tạo lead', compute="_get_type_get_lead", store=True)
    date_open_lead = fields.Datetime(string='Ngày giao lead', compute="_get_type_get_lead", store=True)

    @api.depends('sale_id.type_get_lead')
    def _get_type_get_lead(self):
        for s in self:
            if s.sale_id:
                s.type_get_lead = s.sale_id.type_get_lead
                s.create_lead = s.sale_id.create_lead
                s.date_open_lead = s.sale_id.date_open_lead
            else:
                s.type_get_lead = 'new'
                s.create_lead = s.invoice_date
                s.date_open_lead = s.invoice_date


class LeadBooking(models.Model):
    _inherit = 'crm.lead.booking'

    department_id = fields.Many2one('hr.department', string='Phòng ban')
    create_lead = fields.Datetime(string='Ngày tạo lead', compute="_get_type_get_lead", store=True)
    date_open_lead = fields.Datetime(string='Ngày giao lead', compute="_get_type_get_lead", store=True)

    @api.onchange('department_id')
    def onchange_department(self):
        if not self.department_id:
            self.department_id = self.user_id.employee_id.department_id

    type_get_lead = fields.Selection(selection=[('new', 'Mới'),
                                                ('old', 'Cũ'),
                                                ('create', 'Tự tạo'),
                                                ],
                                     string='Loại lấy lead', compute="_get_type_get_lead", store=True)

    @api.depends('lead_id')
    def _get_type_get_lead(self):
        for s in self:
            if s.lead_id:
                s.type_get_lead = s.lead_id.type_get_lead
                s.create_lead = s.lead_id.create_date
                s.date_open_lead = s.lead_id.date_open
            else:
                s.type_get_lead = 'new'
                s.create_lead = s.date_sent
                s.date_open_lead = s.date_sent


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    type_get_lead = fields.Selection(selection=[('new', 'Mới'),
                                                ('old', 'Cũ'),
                                                ('create', 'Tự tạo'),
                                                ],
                                     string='Loại lấy lead', compute="_get_type_get_lead", store=True)

    @api.depends('opportunity_id')
    def _get_type_get_lead(self):
        for s in self:
            if s.opportunity_id:
                s.type_get_lead = s.opportunity_id.type_get_lead
            else:
                s.type_get_lead = 'new'


class Lead(models.Model):
    _inherit = 'crm.lead'

    department_id = fields.Many2one('hr.department', string='Phòng ban')
    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh')
    year_old = fields.Char(string='Tuổi', default='00/00/1900')
    job_id = fields.Many2one('crm.lead.job', string='Nghề nghiệp')
    type_get_lead = fields.Selection(selection=[('new', 'Mới'),
                                                ('old', 'Cũ'),
                                                ('create', 'Tự tạo'),
                                                ],
                                     string='Loại lấy lead', default='new')
    old_lead_id = fields.Many2one('crm.lead', string='Tham chiếu lead cũ')
    lead_get = fields.Boolean(string='Lead đã lấy', default=False)
    is_old_lead = fields.Boolean(string='Lead cũ', compute='_get_old_lead', store=True)

    @api.depends('stage_id', 'create_date')
    def _get_old_lead(self):
        for s in self:
            date_10 = datetime.now() - timedelta(days=10)
            if s.stage_id.id in (2, 14, 5, 9) and s.create_date < date_10 and s.type_lead == 'sale':
                s.is_old_lead = True
            else:
                s.is_old_lead = False

    @api.model
    def create(self, vals):
        date_1 = datetime.now() - timedelta(days=1)
        # lead_sid = self.env['crm.lead'].sudo().search_count(
        #     [('phone', '=', vals.get('phone')), ('marketing_id', '=', self._uid), ('create_date', '>=', date_1)])
        # if lead_sid:
        #     raise ValidationError("%s Đã được nhập trước đó, bạn không được nhập thêm!!!"
        #                           % (vals.get('phone')))
        lead_id = super(Lead, self).create(vals)
        if lead_id.user_id.id == lead_id.marketing_id.id:
            lead_id.type_get_lead = 'create'
        return lead_id

    def write(self, vals):
        for lead_id in self:
            if lead_id.user_id.id == lead_id.marketing_id.id:
                vals.update({
                    'type_get_lead': 'create'
                })
            res = super(Lead, self).write(vals)
            return res

    @api.onchange('department_id')
    def onchange_department(self):
        if not self.department_id:
            employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)])
            self.department_id = employee_id.department_id

    def get_new_lead(self):
        view_notification_id = self.env.ref('vtg_crm_get_lead.vtg_crm_lead_notification_form_view').id
        division_department_id = self.env['crm.lead.division.department.detail'].search(
            [('department_id', '=', self.env.user.employee_id.department_id.id)])
        # if division_department_id.lead_department_count >= division_department_id.lead_get:
        #     notification_id = self.env['crm.lead.notification'].create({
        #         'name': 'Bộ phận của bạn đã hết số lượng lead để lấy!!!'
        #     })
        #     return {
        #         'type': 'ir.actions.act_window',
        #         'res_model': 'crm.lead.notification',
        #         'view_type': 'form',
        #         'view_mode': 'form',
        #         'views': [(view_notification_id, 'form')],
        #         'target': 'new',
        #         'res_id': notification_id.id,
        #         'context': dict(self._context),
        #     }
        lead_get_count = self.env['crm.lead'].sudo().search_count(
            [('date_open', '>=', date.today()), ('user_id', '=', self._uid)])
        _logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        _logger.info(self.env.user.employee_id.name)
        _logger.info(lead_get_count)
        view_notification_id = self.env.ref('vtg_crm_get_lead.vtg_crm_lead_notification_form_view').id
        notification_id = self.env['crm.lead.notification'].create({
            'name': 'Bạn chưa được thiết lập chia lead trong ngày, Vui lòng liên hệ trưởng nhóm hoặc Giám đốc kinh doanh!!!'
        })
        division_line_id = self.env['crm.lead.division.line'].sudo().search(
            [('date', '=', date.today()), ('user_id', '=', self._uid), ('ok', '=', True)], limit=1)
        _logger.info(division_line_id.qty_lead)
        _logger.info(division_line_id.division_id)

        if not division_line_id or division_line_id.qty_lead <= lead_get_count:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead.notification',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_notification_id, 'form')],
                'target': 'new',
                'res_id': notification_id.id,
                'context': dict(self._context),
            }

        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)])
        department_id = employee_id.department_id

        domain = []
        # if employee_id.job_id.department_get_lead_ids:
        #     domain.append(('department_id', 'in', employee_id.job_id.department_get_lead_ids.ids))
        #     # lead_id = self.env['crm.lead'].sudo().search(
        #     #     [('type_lead', '!=', 'resale'), ('type', '=', 'lead'),
        #     #      ], limit=1,
        #     #     order='create_date ASC')
        # if employee_id.job_id.marketing_get_lead_ids:
        #     domain.append(('marketing_id', 'in', employee_id.job_id.marketing_get_lead_ids.ids))
        #     # lead_id = self.env['crm.lead'].sudo().search(
        #     #     [('type_lead', '!=', 'resale'), ('type', '=', 'lead'),
        #     #      ('marketing_id', 'in', employee_id.job_id.marketing_get_lead_ids.ids)], limit=1,
        #     #     order='create_date ASC')
        # if employee_id.job_id.source_get_lead_ids:
        #     domain.append(('source_id', 'in', employee_id.job_id.source_get_lead_ids.ids))

            # lead_id = self.env['crm.lead'].sudo().search(
            #     [('type_lead', '!=', 'resale'), ('type', '=', 'lead'),
            #      ('source_id', 'in', employee_id.job_id.source_get_lead_ids.ids)], limit=1,
            #     order='create_date ASC')

        # if employee_id.job_id.channel_get_lead_ids:
        #     domain.append(('channel_id', 'in', employee_id.job_id.channel_get_lead_ids.ids))
        # if domain:
        #     domain.append(('type_lead', '!=', 'resale'))
        #     domain.append(('type', '=', 'lead'))
        #     _logger.info(domain)
        #     lead_id = self.env['crm.lead'].sudo().search(
        #         domain, limit=1,
        #         order='create_date ASC')
        # if not employee_id.job_id.department_get_lead_ids \
        #         and not employee_id.job_id.source_get_lead_ids \
        #         and not employee_id.job_id.channel_get_lead_ids \
        #         and not employee_id.job_id.marketing_get_lead_ids:
        lead_id = self.env['crm.lead'].sudo().search(
            [('user_id', '=', self._uid), ('type_lead', '!=', 'resale'), ('type', '=', 'lead')], limit=1, order='create_date ASC')
        if not lead_id:
            lead_id = self.env['crm.lead'].sudo().search(
                [('user_id', '=', False), ('type_lead', '!=', 'resale'), ('type', '=', 'lead')], limit=1, order='create_date ASC')

        user_id = self.env['res.users'].sudo().search([('id', '=', self._uid)])
        lead_id.user_id = self._uid
        lead_id.type = 'opportunity'
        lead_id.date_open = datetime.now()
        lead_id.team_id = user_id.sale_team_id.id
        lead_id.department_id = department_id.id
        lead_id.type_get_lead = 'new'
        view_id = self.env.ref('crm.crm_lead_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': lead_id.id,
            'context': dict(self._context),
        }

    def get_old_lead(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self._uid)])
        department_id = employee_id.department_id
        date_10 = datetime.now() - timedelta(days=30)
        lead_id = self.env['crm.lead'].sudo().search(
            [('stage_id', 'in', (2, 14, 5)),
             ('department_id', '=', department_id.id),
             ('create_date', '<', date_10),
             ('user_id', '!=', self._uid),
             ('type_lead', '=', 'sale'),
             ('old_lead_id', '=', False),
             ('lead_get', '=', False),
             ], limit=1)
        vals = {
            'user_id': self._uid,
            'type_get_lead': 'old',
            'old_lead_id': lead_id.id
        }
        lead_id.lead_get = True
        lead_dup_id = lead_id.copy(default=vals)
        view_id = self.env.ref('crm.crm_lead_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': lead_dup_id.id,
            'context': dict(self._context),
        }


class CRMNOTI(models.TransientModel):
    _name = 'crm.lead.notification'

    name = fields.Char(tring='Thông báo')
