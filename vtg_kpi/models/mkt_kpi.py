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
import calendar



# class CRMLEADINHERIT(models.Model):
#     _inherit = 'crm.lead'
#
#     def write(self, vals):
#         for lead_id in self:
#             res = super(CRMLEADINHERIT, self).write(vals)
#             date_open = lead_id.date_open or lead_id.create_date or datetime.now()
#             kpi_mkt_ids = self.env['crm.kpi.mkt'].sudo().search(
#                 [('user_id', '=', lead_id.marketing_id.id), ('date_start', '<', date_open),
#                  ('date_end', '>', date_open - relativedelta(hours=23))])
#             for kpi_mkt_id in kpi_mkt_ids:
#                 query = """SELECT COUNT(*) lead_count
#                             FROM crm_lead
#                             WHERE create_date >= %s
#                             AND create_date <= %s
#                             AND stage_id not in (16)
#                             AND marketing_id = %s """
#                 self._cr.execute(query, (kpi_mkt_id.date_start, kpi_mkt_id.date_end + relativedelta(days=1), kpi_mkt_id.user_id.id))
#                 lead_counts = self._cr.fetchone()
#                 kpi_mkt_id.qty_lead = lead_counts[0]
#                 if kpi_mkt_id.qty_lead > 0:
#                     kpi_mkt_id.amount_per_lead = kpi_mkt_id.budget / kpi_mkt_id.qty_lead
#                 # UPDATE LINE
#                 for line in kpi_mkt_id.line_ids:
#                     qty_lead = kpi_mkt_id._count_lead(
#                         line.date_start,
#                         line.date_end + relativedelta(days=1),
#                         line.user_id)
#                     line.qty_lead = qty_lead
#                 # UPDATE LINE DAY
#                 for line in kpi_mkt_id.line_day_ids:
#                     qty_lead = kpi_mkt_id._count_lead(
#                         line.date,
#                         line.date + relativedelta(hours=23),
#                         line.user_id)
#                     line.qty_lead = qty_lead
#             return res

class CRMKpiMkt(models.Model):
    _name = 'crm.kpi.mkt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    @api.model
    def _get_default_code(self):
        return self.env["ir.sequence"].next_by_code("crm.kpi.mkt")

    name = fields.Char(string='Tên KPI', track_visibility='onchange')
    date_start = fields.Date(string="Thời gian bắt đầu", required=True)
    date_end = fields.Date(string="Thời gian kết thúc", required=True)
    user_id = fields.Many2one('res.users', string='Nhân viên', required=True, default=lambda self: self.env.user)
    qty_lead_target = fields.Integer(string='Số Lead hợp lệ kế hoạch', required=True)
    qty_lead = fields.Integer(string='Số Lead hợp lệ thực tế')
    qty_lead_percent = fields.Integer(string='Tỉ lệ đạt')
    currency_id = fields.Many2one('res.currency', string='tiền tệ', default=23)
    line_ids = fields.One2many('crm.kpi.mkt.line', 'kpi_id', string='Chi tiết KPI')
    line_day_ids = fields.One2many('crm.kpi.mkt.line.day', 'kpi_id', string='Chi tiết theo ngày')
    amount_per_lead_target = fields.Integer(string='Giá/ Lead hợp lệ kế hoạch', required=True)
    amount_per_lead = fields.Integer(string='Giá/ Lead hợp lệ thực tế')
    budget_target = fields.Integer(string='Ngân sách chi tiêu kế hoạch', required=True)
    budget = fields.Integer(string='Ngân sách chi tiêu thực tế')
    month = fields.Selection([
        ('01', 'Tháng 1'),
        ('02', 'Tháng 2'),
        ('03', 'Tháng 3'),
        ('04', 'Tháng 4'),
        ('05', 'Tháng 5'),
        ('06', 'Tháng 6'),
        ('07', 'Tháng 7'),
        ('08', 'Tháng 8'),
        ('09', 'Tháng 9'),
        ('10', 'Tháng 10'),
        ('11', 'Tháng 11'),
        ('12', 'Tháng 12'),
    ], string='Tháng', default='01', track_visibility='onchange')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Xác nhận'),
        ('cancel', 'Từ chối')
    ], string='Trạng thái', default='draft', track_visibility='onchange')

    def _get_nextcall_monthly_leave(self, month):
        date_1 = date.today()
        start_date = datetime(date_1.year, month, 1)
        end_date = datetime(date_1.year, month, calendar.mdays[month])
        return start_date, end_date

    @api.onchange('month', 'user_id')
    def onchange_state_end_date(self):
        if self.month:
            self.date_start, self.date_end = self._get_nextcall_monthly_leave(int(self.month))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('crm.kpi.mkt') or '/'
        kpi = super(CRMKpiMkt, self).create(vals)
        return kpi

    def action_confirm(self):
        self.state = 'confirmed'

    def action_cancel(self):
        self.state = 'cancel'

    @api.onchange('date_start', 'date_end', 'user_id')
    def _onchange_lead_count(self):
        for s in self:
            if s.date_start and s.date_end:
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('marketing_id', '=', s.user_id.id), ('create_date', '>=', s.date_start),
                     ('create_date', '<=', s.date_end), ('stage_id', '!=', 16)])
                qty_lead = 0
                for lead_id in lead_ids:
                    qty_lead += 1
                s.qty_lead = qty_lead

                budget_ids = self.env['crm.kpi.mkt.budget'].sudo().search(
                    [('user_id', '=', s.user_id.id), ('date', '>=', s.date_start),
                     ('date', '<=', s.date_end)])
                budget = 0
                for budget_id in budget_ids:
                    budget += budget_id.budget
                s.budget = budget
                if s.qty_lead > 0:
                    s.amount_per_lead = budget / s.qty_lead
                if self.line_ids:
                    self.line_ids = None
                self.onchange_state_end_date_create_line(s.date_start, s.date_end)
                if self.line_day_ids:
                    self.line_day_ids = None
                self.onchange_line_day_auto_create(s.user_id, s.date_start, s.date_end)

    def onchange_line_day_auto_create(self, user_id, date_start, date_end):
        day = (date_end - date_start)
        if day != 0:
            vals_add = []
            for n in range(int(day.days) + 1):
                qty_lead = self._count_lead(date_start + relativedelta(days=n),
                                            date_start + relativedelta(days=n), user_id)
                budget = self._sum_budget(date_start + relativedelta(days=n),
                                          date_start + relativedelta(days=n), user_id)
                amount_per_lead = 0
                if qty_lead > 0:
                    amount_per_lead = budget / qty_lead
                vals = {
                    'kpi_id': self.id,
                    'date': date_start + relativedelta(days=n),
                    'qty_lead': qty_lead,
                    'user_id': user_id.id,
                    'budget': budget,
                    'amount_per_lead': amount_per_lead,
                }
                vals_add.append((0, 0, vals))
            self.line_day_ids = vals_add

    @api.onchange('budget_target', 'qty_lead_target')
    def _onchange_amount_per_lead_target(self):
        if self.qty_lead_target > 0:
            self.amount_per_lead_target = self.budget_target / self.qty_lead_target

    @api.onchange('qty_lead_target', 'date_start', 'date_end')
    def onchange_qty_lead_target_per_week(self):
        if self.qty_lead_target:
            qty_lead_target_per_week = self.qty_lead_target / len(self.line_ids)
            for line in self.line_ids:
                if line.qty_lead_target == 0:
                    line.qty_lead_target = qty_lead_target_per_week

    @api.onchange('amount_per_lead_target', 'date_start', 'date_end')
    def onchange_amount_per_lead_target_per_week(self):
        if self.amount_per_lead_target:
            for line in self.line_ids:
                if line.amount_per_lead_target == 0:
                    line.amount_per_lead_target = self.amount_per_lead_target

    @api.onchange('budget_target', 'date_start', 'date_end')
    def onchange_budget_target_per_week(self):
        if self.budget_target:
            budget_target_per_week = self.budget_target / len(self.line_ids)
            for line in self.line_ids:
                if line.budget_target == 0:
                    line.budget_target = budget_target_per_week

    @api.onchange('date_start', 'date_end', 'user_id', 'qty_lead_target')
    def _onchange_lead_count_percent(self):
        for s in self:
            if s.date_start and s.date_end:
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('marketing_id', '=', s.user_id.id), ('create_date', '>=', s.date_start),
                     ('create_date', '<=', s.date_end), ('stage_id', '!=', 16)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                if s.qty_lead_target > 0:
                    s.qty_lead_percent = (lead_count / s.qty_lead_target) * 100
                else:
                    s.qty_lead_percent = 0

    def _count_lead(self, date_start, date_end, user_id):
        lead_ids = self.env['crm.lead'].sudo().search(
            [('marketing_id', '=', user_id.id), ('create_date', '>=', date_start),
             ('create_date', '<=', date_end), ('stage_id', '!=', 16)])
        lead_count = 0
        for lead_id in lead_ids:
            lead_count += 1
        return lead_count

    def _sum_budget(self, date_start, date_end, user_id):
        budget_ids = self.env['crm.kpi.mkt.budget'].sudo().search(
            [('user_id', '=', user_id.id), ('date', '>=', date_start),
             ('date', '<=', date_end)])
        budget = 0
        for budget_id in budget_ids:
            budget += budget_id.budget
        return budget

    def onchange_state_end_date_create_line(self, date_start, date_end):
        if date_start and date_end:
            if date_start and date_start + relativedelta(weeks=1) <= date_end:
                qty_lead = self._count_lead(date_start, date_start + relativedelta(weeks=1), self.user_id)
                budget = self._sum_budget(date_start, date_start + relativedelta(weeks=1), self.user_id)
                vals = {
                    'week': '01',
                    'date_start': date_start,
                    'date_end': date_start + relativedelta(weeks=1),
                    'qty_lead_target': 0,
                    'qty_lead': qty_lead,
                    'amount_per_lead_target': 0,
                    'amount_per_lead': 0,
                    'budget_target': 0,
                    'budget': budget,
                    'user_id': self.user_id.id,
                    'kpi_id': self.id,
                }
                self.update({'line_ids': [(0, 0, vals)]})
            if date_start and date_start + relativedelta(weeks=2) <= date_end:
                qty_lead = self._count_lead(date_start + relativedelta(weeks=1), date_start + relativedelta(weeks=2),
                                            self.user_id)
                budget = self._sum_budget(date_start + relativedelta(weeks=1), date_start + relativedelta(weeks=2),
                                          self.user_id)

                vals = {
                    'week': '02',
                    'date_start': date_start + relativedelta(weeks=1),
                    'date_end': date_start + relativedelta(weeks=2),
                    'qty_lead_target': 0,
                    'qty_lead': qty_lead,
                    'amount_per_lead_target': 0,
                    'amount_per_lead': 0,
                    'budget_target': 0,
                    'budget': budget,
                    'user_id': self.user_id.id,
                    'kpi_id': self.id,
                }
                self.update({'line_ids': [(0, 0, vals)]})
                if date_start and date_start + relativedelta(weeks=3) <= date_end:
                    qty_lead = self._count_lead(date_start + relativedelta(weeks=2),
                                                date_start + relativedelta(weeks=3),
                                                self.user_id)
                    budget = self._sum_budget(date_start + relativedelta(weeks=2),
                                              date_start + relativedelta(weeks=3),
                                              self.user_id)
                    vals = {
                        'week': '03',
                        'date_start': date_start + relativedelta(weeks=2),
                        'date_end': date_start + relativedelta(weeks=3),
                        'qty_lead_target': 0,
                        'qty_lead': qty_lead,
                        'amount_per_lead_target': 0,
                        'amount_per_lead': 0,
                        'budget_target': 0,
                        'budget': budget,
                        'user_id': self.user_id.id,
                        'kpi_id': self.id,
                    }
                    self.update({'line_ids': [(0, 0, vals)]})

                if date_start and date_start + relativedelta(weeks=4) <= date_end:
                    qty_lead = self._count_lead(date_start + relativedelta(weeks=3),
                                                date_start + relativedelta(weeks=4),
                                                self.user_id)
                    budget = self._sum_budget(date_start + relativedelta(weeks=3),
                                              date_start + relativedelta(weeks=4),
                                              self.user_id)

                    vals = {
                        'week': '04',
                        'date_start': date_start + relativedelta(weeks=3),
                        'date_end': date_start + relativedelta(weeks=4),
                        'qty_lead_target': 0,
                        'qty_lead': qty_lead,
                        'amount_per_lead_target': 0,
                        'amount_per_lead': 0,
                        'budget_target': 0,
                        'budget': budget,
                        'user_id': self.user_id.id,
                        'kpi_id': self.id,
                    }
                    self.update({'line_ids': [(0, 0, vals)]})
                if date_start and date_start + relativedelta(weeks=5) <= date_end:
                    qty_lead = self._count_lead(date_start + relativedelta(weeks=4),
                                                date_start + relativedelta(weeks=5),
                                                self.user_id)
                    budget = self._sum_budget(date_start + relativedelta(weeks=4),
                                              date_start + relativedelta(weeks=5),
                                              self.user_id)

                    vals = {
                        'week': '05',
                        'date_start': date_start + relativedelta(weeks=4),
                        'date_end': date_end,
                        'qty_lead_target': 0,
                        'qty_lead': qty_lead,
                        'amount_per_lead_target': 0,
                        'amount_per_lead': 0,
                        'budget_target': 0,
                        'budget': budget,
                        'user_id': self.user_id.id,
                        'kpi_id': self.id,
                    }
                    self.update({'line_ids': [(0, 0, vals)]})


class CRMKpisaleLine(models.Model):
    _name = 'crm.kpi.mkt.line'

    kpi_id = fields.Many2one('crm.kpi.mkt', string='KPI')
    week = fields.Selection([
        ('01', 'Tuần 1'),
        ('02', 'Tuần 2'),
        ('03', 'Tuần 3'),
        ('04', 'Tuần 4'),
        ('05', 'Tuần 5'),
    ], string='Tuần', default='01', track_visibility='onchange')
    date_start = fields.Date(string="Bắt đầu", required=True)
    date_end = fields.Date(string="Kết thúc", required=True)
    user_id = fields.Many2one('res.users', string='Nhân viên')
    qty_lead_target = fields.Integer(string='Số Lead hợp lệ kế hoạch', required=True)
    qty_lead = fields.Integer(string='Số Lead hợp lệ thực tế')
    currency_id = fields.Many2one('res.currency', string='tiền tệ', default=23)
    amount_per_lead_target = fields.Integer(string='Giá/ Lead hợp lệ kế hoạch', required=True)
    amount_per_lead = fields.Integer(string='Giá/ Lead hợp lệ thực tế')
    budget_target = fields.Integer(string='Ngân sách chi tiêu kế hoạch', required=True)
    budget = fields.Integer(string='Ngân sách chi tiêu thực tế')


class CRMKpiMKTLineDay(models.Model):
    _name = 'crm.kpi.mkt.line.day'

    kpi_id = fields.Many2one('crm.kpi.mkt', string='KPI')
    date = fields.Date(string="Ngày", required=True)
    user_id = fields.Many2one('res.users', string='Nhân viên')
    qty_lead = fields.Integer(string='Số Lead hợp lệ thực tế')
    currency_id = fields.Many2one('res.currency', string='tiền tệ', default=23)
    amount_per_lead = fields.Integer(string='Giá/ Lead hợp lệ thực tế')
    budget = fields.Integer(string='Ngân sách chi tiêu thực tế')
    qty_lead_kh = fields.Integer(string='Số Lead kế hoạch', store=True, compute="_qty_lead_kh")
    qty_lead_tt = fields.Integer(string='Số Lead hợp lệ thực tế', store=True, compute="_qty_lead_kh")
    amount_per_lead_target = fields.Integer(string='Giá/ Lead hợp lệ kế hoạch', store=True, compute="_amount_per_lead")
    amount_per_lead_sum = fields.Integer(string='Giá/ Lead hợp lệ thực tế', store=True, compute="_amount_per_lead")

    @api.depends('kpi_id.amount_per_lead_target', 'kpi_id.amount_per_lead')
    def _amount_per_lead(self):
        """
        Compute the total amounts of the SO.
        """
        for day in self:
            day.update({
                'amount_per_lead_target': day.kpi_id.amount_per_lead_target,
                'amount_per_lead_sum': day.kpi_id.amount_per_lead,
            })

    @api.depends('kpi_id.qty_lead_target','kpi_id.qty_lead')
    def _qty_lead_kh(self):
        """
        Compute the total amounts of the SO.
        """
        for day in self:
            day.update({
                'qty_lead_kh': day.kpi_id.qty_lead_target,
                'qty_lead_tt': day.kpi_id.qty_lead,
            })

class CRMKpiMktbudgetChannel(models.Model):
    _name = 'crm.kpi.mkt.budget.channel'

    name = fields.Char(string='Tên kênh')

class CRMUTMSOURCE(models.Model):
    _inherit = 'utm.source'

    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel',string='Kênh')

class CRMKpiMktbudget(models.Model):
    _name = 'crm.kpi.mkt.budget'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    @api.model
    def _get_default_code(self):
        return self.env["ir.sequence"].next_by_code("crm.kpi.mkt.budget")

    name = fields.Char(string='Mã')
    date = fields.Date(string="Ngày", required=True, default=fields.Date.today())
    user_id = fields.Many2one('res.users', string='Nhân viên', required=True, default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department', string='Phòng', required=True,default=lambda self: self.env.user.employee_id.department_id)
    reason = fields.Text('Lý do chi tiêu')
    budget = fields.Integer(string='Giá trị chi tiêu')
    id_invoice = fields.Char(string='ID thanh toán')
    img_invoice = fields.Binary(string='Ảnh hóa đơn')
    currency_id = fields.Many2one('res.currency', string='tiền tệ', default=23)
    source_id = fields.Many2one('utm.source', string='Nguồn')
    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('crm.kpi.mkt.budget') or '/'
        kpi = super(CRMKpiMktbudget, self).create(vals)
        return kpi

    @api.model
    def create(self, vals):
        budget_id = super(CRMKpiMktbudget, self).create(vals)
        date = budget_id.date or budget_id.create_date
        kpi_mkt_ids = self.env['crm.kpi.mkt'].sudo().search(
            [('user_id', '=', budget_id.user_id.id), ('date_start', '<', date),
             ('date_end', '>', date)])
        for kpi_mkt_id in kpi_mkt_ids:
            query = """ SELECT SUM(budget) budget
                         FROM crm_kpi_mkt_budget
                         WHERE date >= %s
                         AND date <= %s
                         AND user_id = %s """
            self._cr.execute(query, (kpi_mkt_id.date_start, kpi_mkt_id.date_end, kpi_mkt_id.user_id.id))
            budget = self._cr.fetchone()
            kpi_mkt_id.budget = budget[0]
            if kpi_mkt_id.qty_lead > 0:
                kpi_mkt_id.amount_per_lead = kpi_mkt_id.budget / kpi_mkt_id.qty_lead
        return budget_id

    def write(self, vals):
        for budget_id in self:
            res = super(CRMKpiMktbudget, self).write(vals)
            date = budget_id.date or budget_id.create_date
            kpi_mkt_ids = self.env['crm.kpi.mkt'].sudo().search(
                [('user_id', '=', budget_id.user_id.id), ('date_start', '<', date),
                 ('date_end', '>', date)])
            for kpi_mkt_id in kpi_mkt_ids:
                query = """ SELECT SUM(budget) budget
                             FROM crm_kpi_mkt_budget
                             WHERE date >= %s
                             AND date <= %s
                             AND user_id = %s """
                self._cr.execute(query, (kpi_mkt_id.date_start, kpi_mkt_id.date_end, kpi_mkt_id.user_id.id))
                budget = self._cr.fetchone()
                kpi_mkt_id.budget = budget[0]
                if kpi_mkt_id.qty_lead > 0:
                    kpi_mkt_id.amount_per_lead = kpi_mkt_id.budget / kpi_mkt_id.qty_lead
            return res
