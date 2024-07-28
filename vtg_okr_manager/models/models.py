# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, SUPERUSER_ID, http, _
from odoo.http import request
from odoo.exceptions import except_orm, ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import calendar
import logging
from odoo.exceptions import RedirectWarning, UserError, ValidationError

_logger = logging.getLogger(__name__)


class OKRManager(models.Model):
    _name = 'dpt.okr.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    @api.model
    def _get_default_code(self):
        return self.env["ir.sequence"].next_by_code("dpt.kpi.manager")

    def _get_default_member_ids(self):

        user_member_ids = self.env['res.users'].sudo().search([]).filtered(
            lambda x: x.active and not x.has_group('to_sales_team_advanced.group_sale_team_leader'))
        ids = []
        for ul in user_member_ids:
            if not ul.sale_team_id:
                ids.append(ul.id)
        domain = [('id', 'in', ids)]
        user_ids = self.env['res.users'].sudo().search(domain)
        return user_ids

    name = fields.Char(string='Name')
    okr_code = fields.Char(string='Mã OKR', required=True, default='/', copy=False)
    parent_id = fields.Many2one('dpt.okr.manager', string='Mục tiêu tầng trên',
                                domain=[('state', 'not in', ['draft', 'cancel'])], tracking=True)
    child_ids = fields.One2many('dpt.okr.manager', 'parent_id', string='Childs', ondelete='cascade', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', tracking=True)
    department_id = fields.Many2one('hr.department', string='Phòng', tracking=True)
    start_date = fields.Date(string='Start date', default=datetime.now(), tracking=True)
    end_date = fields.Date(default=datetime.now(), tracking=True)
    description = fields.Text(string='Description', widget="html")
    deadline = fields.Date(string='Deadline', default=datetime.now(), tracking=True)
    time_type = fields.Selection(selection=[('days', 'Ngày'),
                                            ('week', 'Tuần'),
                                            ('month', 'Tháng'),
                                            ('precious', 'Quí'),
                                            ('year', 'Năm'),
                                            ], default='days', string='Loại thời gian', tracking=True)
    type_okr = fields.Selection(selection=[('employee', 'Cá nhân'),
                                           ('team', 'Nhóm'),
                                           ('department', 'Phòng'),
                                           ('company', 'Công ty')
                                           ], default='employee', string='Loại mục tiêu', tracking=True)
    year = fields.Selection(selection=
                            [(str(num), 'Năm ' + str(num)) for num in
                             range((datetime.now().year), (datetime.now().year) + 5)], string='Năm'
                            )
    precious = fields.Selection(selection=[(str(num), 'Quí ' + str(num) + '/' + str(y)) for y in
                                           range((datetime.now().year), (datetime.now().year) + 1) for num in
                                           range(1, 5)],
                                string='Quí'
                                )
    month = fields.Selection(selection=[(str(num), 'Tháng ' + str(num) + '/' + str(y)) for y in
                                        range((datetime.now().year), (datetime.now().year) + 1) for num in
                                        range(1, 13)],
                             string='Tháng')

    week = fields.Selection(selection=[(str(num) + '/' + str(m), 'Tuần ' + str(num) + '/ Tháng' + str(m)) for m in
                                       range((datetime.now().month), (datetime.now().month) + 3) for num in
                                       range(1, 5)],
                            string='Tháng')
    day = fields.Date(string='Ngày', default=lambda d: date.today(), tracking=True)
    kpi_line_ids = fields.One2many('dpt.kpi.manager', 'okr_id', string='Chỉ số (Kết quả/KPI)', copy=True)
    state = fields.Selection(selection=[('draft', 'Mục tiêu nháp'),
                                        ('wait_confirm', 'Mục tiêu chờ duyệt'),
                                        ('not_confirm', 'Mục tiêu không được duyệt'),
                                        ('confirmed', 'Mục tiêu được chốt'),
                                        ('cancel', 'Hủy'),
                                        ], default='draft', string='State', tracking=True)
    reason_cancel = fields.Text(strin='Reason cancel')
    percent = fields.Float(string='Tỉ lệ hoàn thành Chỉ số', compute="_compute_percent")
    x_domain_member_ids = fields.Many2many('res.users', 'domain_okr_member_res_users_rel', 'user_id',
                                           'okr_id', string='Domain res users',
                                           default=_get_default_member_ids, compute='_compute_domain_member_ids')

    x_is_view = fields.Boolean(default=False, compute="_compute_x_is_view")

    @api.depends('x_is_view')
    def _compute_x_is_view(self):
        for okr in self:
            if self.env.user.has_group('vtg_security.group_vtg_employee_sale') or self.env.user.has_group(
                    'vtg_security.group_vtg_employee_cashier') or self.env.user.has_group('vtg_security.group_vtg_employee_mkt'):
                if self.env.user.employee_id == okr.employee_id:
                    okr.x_is_view = True
                    okr.parent_id.x_is_view = True
                elif self.env.user.employee_id.department_id.manager_id == okr.employee_id:
                    okr.x_is_view = True
                    okr.parent_id.x_is_view = True
                elif self.env.user.employee_id.department_id.manager_id == okr.employee_id:
                    okr.x_is_view = True
                    okr.parent_id.x_is_view = True
                elif okr.employee_id.user_id.has_group('vtg_security.group_vtg_director'):
                    okr.x_is_view = True
                    okr.parent_id.x_is_view = True

                else:
                    okr.x_is_view = False
            elif self.env.user.has_group('vtg_security.group_vtg_employee_team_sale'):
                if self.env.user.sale_team_id == okr.employee_id.user_id.sale_team_id:
                    okr.x_is_view = True
                    okr.parent_id.x_is_view = True
                else:
                    okr.x_is_view = False
            elif self.env.user.has_group('vtg_security.group_vtg_director_sale'):
                if self.env.user.employee_id.department_id == okr.department_id:
                    okr.x_is_view = True
                    okr.parent_id.x_is_view = True
                else:
                    okr.x_is_view = False
            elif self.env.user.has_group('vtg_security.group_vtg_director'):
                okr.x_is_view = True

    @api.depends('x_domain_member_ids')
    def _compute_domain_member_ids(self):
        for rc in self:
            user_member_ids = self.env['res.users'].sudo().search([]).filtered(
                lambda x: x.active and not x.has_group(
                    'to_sales_team_advanced.group_sale_team_leader') and not x.sale_team_id)

            user_leader_ids = self.env['res.users'].sudo().search([]).filtered(
                lambda x: x.active and x.has_group('to_sales_team_advanced.group_sale_team_leader') and not x.has_group(
                    'sales_team.group_sale_salesman_all_leads'))
            ids = []
            for i in user_leader_ids:
                ids.append(i.id)

            for mem_id in user_member_ids:
                ids.append(mem_id.id)
            domain = [('id', 'in', ids)]
            user_ids = self.env['res.users'].sudo().search(domain)
            rc.x_domain_member_ids = user_ids

    @api.depends('is_view_okr')
    def _compute_view_okr(self):
        for s in self:
            if self.env.user.has_group('vtg_security.group_vtg_employee_sale') \
                    or self.env.user.has_group('vtg_security.group_vtg_employee_cashier') \
                    or self.env.user.has_group('vtg_security.group_vtg_employee_mkt'):
                if self.env.user.id == s.employee_id.user_id.id:
                    s.is_view_okr = True
                elif s.employee_id.id == self.env.user.employee_id.department_id.manager_id.id:
                    s.is_view_okr = True
                else:
                    s.is_view_okr = False
            elif self.env.user.has_group('vtg_security.group_vtg_director_sale'):
                if self.env.user.employee_id.department_id.id == s.department_id.id:
                    s.is_view_okr = True
                elif s.employee_id.user_id.has_group('vtg_security.group_vtg_director'):
                    s.is_view_okr = True
            else:
                s.is_view_okr = False

    @api.depends('kpi_line_ids')
    def _compute_percent(self):
        """
        Compute the percent.
        """
        for day in self:
            value = 0
            result = 0
            for kpi in day.kpi_line_ids:
                value += kpi.value
                result += kpi.result
            if value != 0:
                day.percent = (result / value) * 100
            else:
                day.percent = 0

    def _get_nextcall_monthly_leave(self, month):
        date_1 = date.today()
        start_date = datetime(date_1.year, month, 1)
        end_date = datetime(date_1.year, month, calendar.mdays[month])
        return start_date, end_date

    @api.onchange('month')
    def onchange_state_end_date_month(self):
        if self.month:
            self.start_date, self.end_date = self._get_nextcall_monthly_leave(int(self.month))

    def _get_nextcall_year_leave(self, year):
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        return start_date, end_date

    @api.onchange('year')
    def onchange_state_end_date_year(self):
        if self.year:
            self.start_date, self.end_date = self._get_nextcall_year_leave(int(self.year))

    def _get_nextcall_precious_leave(self, precious):
        date_1 = date.today()
        if precious == 1:
            start_date = datetime(date_1.year, 1, 1)
            end_date = datetime(date_1.year, 3, 31)
        if precious == 2:
            start_date = datetime(date_1.year, 4, 1)
            end_date = datetime(date_1.year, 6, 30)
        if precious == 3:
            start_date = datetime(date_1.year, 7, 1)
            end_date = datetime(date_1.year, 9, 30)
        if precious == 4:
            start_date = datetime(date_1.year, 10, 1)
            end_date = datetime(date_1.year, 12, 31)
        return start_date, end_date

    @api.onchange('precious')
    def onchange_state_end_date_precious(self):
        if self.precious:
            self.start_date, self.end_date = self._get_nextcall_precious_leave(int(self.precious))

    def _get_nextcall_week_leave(self, week):
        date_1 = date.today()
        w = week.split("/")
        if w[0] == '1':
            start_date = datetime(date_1.year, int(w[1]), 1)
            end_date = start_date + relativedelta(weeks=1)
        if w[0] == '2':
            start_date = datetime(date_1.year, int(w[1]), 1) + relativedelta(weeks=1)
            end_date = start_date + relativedelta(weeks=1)
        if w[0] == '3':
            start_date = datetime(date_1.year, int(w[1]), 1) + relativedelta(weeks=2)
            end_date = start_date + relativedelta(weeks=1)
        if w[0] == '4':
            start_date = datetime(date_1.year, int(w[1]), 1) + relativedelta(weeks=3)
            end_date = start_date + relativedelta(weeks=1)
        return start_date, end_date

    @api.onchange('week')
    def onchange_state_end_date_week(self):
        if self.week:
            self.start_date, self.end_date = self._get_nextcall_week_leave(self.week)

    @api.model
    def create(self, vals):
        vals['okr_code'] = self.env['ir.sequence'].next_by_code('dpt.kpi.manager') or '/'
        kpi = super(OKRManager, self).create(vals)
        kpi._check_rule_okr()
        return kpi

    def write(self, vals):
        for kpi in self:
            res = super(OKRManager, self).write(vals)
            kpi._check_rule_okr()
        return res

    def _check_rule_okr(self):
        if self.employee_id.user_id.has_group(
                'vtg_security.group_vtg_employee_sale') or self.employee_id.user_id.has_group(
            'vtg_security.group_vtg_employee_cashier') or self.employee_id.user_id.has_group(
            'vtg_security.group_vtg_employee_mkt'):
            if self.type_okr != 'employee':
                message = ''
                message += f'Bạn chỉ được chọn mục tiêu cá nhân'
                if message:
                    raise UserError(message)
        if self.employee_id.user_id.has_group(
                'vtg_security.group_vtg_employee_team_sale'):
            if self.type_okr not in ('employee', 'team'):
                message = ''
                message += f'Bạn chỉ được chọn mục tiêu cá nhân hoặc nhóm'
                if message:
                    raise UserError(message)
        if self.employee_id.user_id.has_group(
                'vtg_security.group_vtg_director_sale'):
            if self.type_okr not in ('employee', 'team', 'company'):
                message = ''
                message += f'Bạn không được phép chọn mục tiêu Công ty'
                if message:
                    raise UserError(message)

    def action_registered(self):
        self.state = 'wait_confirm'

    def action_confirm(self):
        self.state = 'confirmed'

    def action_cancel(self):
        view_id = self.env.ref('dpt_okr_manager.dpt_okr_reason_cancel_view_from').id
        context = dict(self.env.context).copy()
        return {
            'name': _('OKR Cancel'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'dpt.okr.manager',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.id,
            'context': context,
            'flags': {'form': {'action_buttons': False}, }
        }

    def back_state(self):
        self.state = 'draft'

    def action_reason_cancel(self):
        self.state = 'cancel'

    def write(self, vals):
        for okr_id in self:
            res = super(OKRManager, self).write(vals)
            # for kpi in okr_id.kpi_line_ids:
            okr_id._action_auto_update()
                # if kpi.type == 'lead':
                #     kpi.result = kpi._count_lead(okr_id.start_date,
                #                                  okr_id.end_date, okr_id.employee_id.user_id)
                # if kpi.type == 'amount':
                #     amount_total = kpi._sale_order_amount_reality(
                #         okr_id.start_date,
                #         okr_id.end_date, okr_id.employee_id.user_id)
                #     kpi.result = amount_total
                # if kpi.type == 'total':
                #     total = kpi._sale_order_total(
                #         okr_id.start_date,
                #         okr_id.end_date, okr_id.employee_id.user_id)
                #     kpi.result = total
                # if kpi.type == 'cost':
                #     kpi.result = kpi._sum_cost(okr_id.start_date,
                #                                okr_id.end_date, okr_id.employee_id.user_id)
                # if kpi.type == 'booking':
                #     kpi.result = kpi._count_booking(okr_id.start_date,
                #                                     okr_id.end_date, okr_id.employee_id.user_id)
                # if kpi.type == 'order':
                #     kpi.result = kpi._count_order(okr_id.start_date,
                #                                   okr_id.end_date, okr_id.employee_id.user_id)
            return res

    def _action_auto_update(self):
        for okr_id in self:
            for kpi in okr_id.kpi_line_ids:
                if kpi.type == 'lead':
                    kpi.result = kpi._count_lead(okr_id.start_date,
                                                 okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'lead_new':
                    kpi.result = kpi._count_lead_new(okr_id.start_date,
                                                 okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'lead_old':
                    kpi.result = kpi._count_lead_old(okr_id.start_date,
                                                 okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'amount':
                    amount_total = kpi._sale_order_amount_reality(
                        okr_id.start_date,
                        okr_id.end_date, okr_id.employee_id.user_id)
                    kpi.result = amount_total
                if kpi.type == 'total':
                    total = kpi._sale_order_total(
                        okr_id.start_date,
                        okr_id.end_date, okr_id.employee_id.user_id)
                    kpi.result = total
                if kpi.type == 'cost':
                    kpi.result = kpi._sum_cost(okr_id.start_date,
                                               okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'booking':
                    kpi.result = kpi._count_booking(okr_id.start_date,
                                                    okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'order':
                    kpi.result = kpi._count_order(okr_id.start_date,
                                                  okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'order_cod':
                    kpi.result = kpi._count_order_cod(okr_id.start_date,
                                                  okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'order_direct':
                    kpi.result = kpi._count_order_direct(okr_id.start_date,
                                                  okr_id.end_date, okr_id.employee_id.user_id)

    @api.onchange('employee_id', 'start_date', 'end_date', 'type_okr')
    def onchange_result(self):
        for kpi in self.kpi_line_ids:
            if kpi.type == 'lead':
                kpi.result = kpi._count_lead(self.start_date,
                                             self.end_date, self.employee_id.user_id)
            if kpi.type == 'lead_new':
                kpi.result = kpi._count_lead_new(self.start_date,
                                             self.end_date, self.employee_id.user_id)
            if kpi.type == 'lead_old':
                kpi.result = kpi._count_lead_old(self.start_date,
                                             self.end_date, self.employee_id.user_id)

            if kpi.type == 'amount':
                amount_total = kpi._sale_order_amount_reality(
                    self.start_date,
                    self.end_date, self.employee_id.user_id)
                kpi.result = amount_total
            if kpi.type == 'total':
                total = kpi._sale_order_total(
                    self.start_date,
                    self.end_date, self.employee_id.user_id)
                kpi.result = total
            if kpi.type == 'cost':
                kpi.result = kpi._sum_cost(self.start_date,
                                           self.end_date, self.employee_id.user_id)
            if kpi.type == 'booking':
                kpi.result = kpi._count_booking(self.start_date,
                                                self.end_date, self.employee_id.user_id)
            if kpi.type == 'order':
                kpi.result = kpi._count_order(self.start_date,
                                              self.end_date, self.employee_id.user_id)
            if kpi.type == 'order_cod':
                kpi.result = kpi._count_order_cod(self.start_date,
                                              self.end_date, self.employee_id.user_id)
            if kpi.type == 'order_direct':
                kpi.result = kpi._count_order_direct(self.start_date,
                                              self.end_date, self.employee_id.user_id)


class OKRKPIManager(models.Model):
    _name = 'dpt.kpi.manager'
    _order = 'create_date desc'

    okr_id = fields.Many2one('dpt.okr.manager', string='OKR')
    name = fields.Char(string='Mô tả')
    type = fields.Selection(selection=[
                                       ('lead', 'Tổng số lead'),
                                       ('lead_new', 'Số lead mới'),
                                       ('lead_old', 'Số lead cũ'),
                                       ('amount', 'Doanh thu'),
                                       ('total', 'Doanh số'),
                                       ('cost', 'Chi phí'),
                                       ('booking', 'Booking'),
                                       ('order', 'Tổng Đơn hàng'),
                                       ('order_cod', 'Đơn hàng COD'),
                                       ('order_direct', 'Đơn hàng Trực tiếp'),
                                       ], default='lead', string='Loại', required=True)
    value = fields.Float(string='Chỉ số')
    result = fields.Float(string='Kết quả đạt được')
    percent = fields.Float(string='Tỉ lệ hoàn thành', compute="_compute_percent")

    user_id = fields.Many2one('res.users', string='Nhân viên')
    department_id = fields.Many2one('hr.department', string='Phòng')
    start_date = fields.Date(string='Start date')
    end_date = fields.Date(string='End date')
    time_type = fields.Selection(selection=[('days', 'Ngày'),
                                            ('week', 'Tuần'),
                                            ('month', 'Tháng'),
                                            ('precious', 'Quí'),
                                            ('year', 'Năm'),
                                            ], default='days', string='Loại thời gian')
    type_okr = fields.Selection(selection=[('employee', 'Cá nhân'),
                                           ('team', 'Nhóm'),
                                           ('department', 'Phòng'),
                                           ('company', 'Công ty')
                                           ], default='employee', string='Loại mục tiêu')

    @api.model
    def create(self, vals):
        okr_id = self.env['dpt.okr.manager'].search([('id', '=', self.okr_id.id)])
        vals.update({
            'user_id': okr_id.employee_id.user_id.id,
            'department_id': okr_id.department_id.id,
            'start_date': okr_id.start_date,
            'end_date': okr_id.end_date,
            'time_type': okr_id.time_type,
            'type_okr': okr_id.type_okr,
        })
        kpi = super(OKRKPIManager, self).create(vals)
        return kpi

    def write(self, vals):
        for kpi in self:
            okr_id = self.env['dpt.okr.manager'].search([('id', '=', kpi.okr_id.id)])
            vals.update({
                'user_id': okr_id.employee_id.user_id.id,
                'department_id': okr_id.department_id.id,
                'start_date': okr_id.start_date,
                'end_date': okr_id.end_date,
                'time_type': okr_id.time_type,
                'type_okr': okr_id.type_okr,
            })
            res = super(OKRKPIManager, self).write(vals)
        return res

    @api.depends('result', 'value')
    def _compute_percent(self):
        """
        Compute the percent.
        """
        for kpi in self:
            value = 0
            result = 0
            value += kpi.value
            result += kpi.result
            if value != 0:
                kpi.percent = (result / value) * 100
            else:
                kpi.percent = 0

    def _count_order(self, date_start, date_end, user_id):
        sale_count = 0
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            sale_count = self.env['sale.order'].sudo().search_count(
                [('user_id', '=', user_id.id),
                 ('date_order', '>=', date_start),
                 ('date_order', '<=', date_end)])
            return sale_count
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            sale_count = self.env['sale.order'].sudo().search_count(
                [('opportunity_id.marketing_id', '=', user_id.id),
                 ('opportunity_id.create_date', '>=', date_start),
                 ('opportunity_id.create_date', '<=', date_end), ('type_customer', '=', 'new')])
            return sale_count

        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count

        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'department':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count

        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'company':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'department':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
        return sale_count

    def _count_order_cod(self, date_start, date_end, user_id):
        sale_count = 0
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            sale_count = self.env['sale.order'].sudo().search_count(
                [('user_id', '=', user_id.id),
                 ('type_order', '=', 'cod'),
                 ('date_order', '>=', date_start),
                 ('date_order', '<=', date_end)])
            return sale_count
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            sale_count = self.env['sale.order'].sudo().search_count(
                [('opportunity_id.marketing_id', '=', user_id.id),
                 ('type_order', '=', 'cod'),
                 ('opportunity_id.create_date', '>=', date_start),
                 ('opportunity_id.create_date', '<=', date_end), ('type_customer', '=', 'new')])
            return sale_count

        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('type_order', '=', 'cod'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('type_order', '=', 'cod'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count

        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('type_order', '=', 'cod'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('type_order', '=', 'cod'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'department':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('type_order', '=', 'cod'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count

        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'company':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('date_order', '>=', date_start),
                     ('type_order', '=', 'cod'),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'department':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('date_order', '>=', date_start),
                     ('type_order', '=', 'cod'),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('type_order', '=', 'cod'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('type_order', '=', 'cod'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
        return sale_count

    def _count_order_direct(self, date_start, date_end, user_id):
        sale_count = 0
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            sale_count = self.env['sale.order'].sudo().search_count(
                [('user_id', '=', user_id.id),
                 ('type_order', '=', 'direct'),
                 ('date_order', '>=', date_start),
                 ('date_order', '<=', date_end)])
            return sale_count
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            sale_count = self.env['sale.order'].sudo().search_count(
                [('opportunity_id.marketing_id', '=', user_id.id),
                 ('type_order', '=', 'direct'),
                 ('opportunity_id.create_date', '>=', date_start),
                 ('opportunity_id.create_date', '<=', date_end),
                 ('type_customer', '=', 'new')])
            return sale_count

        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('type_order', '=', 'direct'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('type_order', '=', 'direct'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count

        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('type_order', '=', 'direct'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('type_order', '=', 'direct'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'department':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('type_order', '=', 'direct'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count

        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'company':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('date_order', '>=', date_start),
                     ('type_order', '=', 'direct'),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'department':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('type_order', '=', 'direct'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'team':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('type_order', '=', 'direct'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
            if self.okr_id.type_okr == 'employee':
                sale_count = self.env['sale.order'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('type_order', '=', 'direct'),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                return sale_count
        return sale_count

    def _count_booking(self, date_start, date_end, user_id):
        booking_count = 0
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            booking_count = self.env['crm.lead.booking'].sudo().search_count(
                [('lead_id.marketing_id', '=', user_id.id),
                 ('date_sent', '>=', date_start),
                 ('date_sent', '<=', date_end)])
            return booking_count
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            booking_count = self.env['crm.lead.booking'].sudo().search_count(
                [('user_id', '=', user_id.id),
                 ('date_sent', '>=', date_start),
                 ('date_sent', '<=', date_end)])
            return booking_count

        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count
            if self.okr_id.type_okr == 'team':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count

        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count
            if self.okr_id.type_okr == 'team':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count
            if self.okr_id.type_okr == 'department':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('department_id', '=', user_id.employee_id.department_id.id),
                     ('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count

        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'employee':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('user_id', '=', user_id.id),
                     ('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count
            if self.okr_id.type_okr == 'team':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count
            if self.okr_id.type_okr == 'department':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('user_id', '=', user_id.employee_id.department_id.id),
                     ('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count
            if self.okr_id.type_okr == 'company':
                booking_count = self.env['crm.lead.booking'].sudo().search_count(
                    [('date_sent', '>=', date_start),
                     ('date_sent', '<=', date_end)])
                return booking_count
        return booking_count

    def _sum_cost(self, date_start, date_end, user_id):
        budget = 0
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            cost_ids = self.env['crm.kpi.mkt.budget'].sudo().search(
                [('user_id', '=', user_id.id),
                 ('date', '>=', date_start),
                 ('date', '<=', date_end)])
            budget = 0
            for cost_id in cost_ids:
                budget += cost_id.budget
            return budget
        if user_id.has_group('vtg_security.group_vtg_director_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            cost_ids = self.env['crm.kpi.mkt.budget'].sudo().search(
                [('department_id', '=', user_id.employee_id.department_id.id),
                 ('date', '>=', date_start),
                 ('date', '<=', date_end)])
            budget = 0
            for cost_id in cost_ids:
                budget += cost_id.budget
            return budget
        if user_id.has_group('vtg_security.group_vtg_director'):
            cost_ids = self.env['crm.kpi.mkt.budget'].sudo().search(
                [('date', '>=', date_start),
                 ('date', '<=', date_end)])
            budget = 0
            for cost_id in cost_ids:
                budget += cost_id.budget
            return budget
        return budget

    def _count_lead(self, date_start, date_end, user_id):
        lead_count = 0
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            lead_ids = self.env['crm.lead'].sudo().search(
                [('user_id', '=', user_id.id),
                 ('date_open', '>=', date_start),
                 ('date_open', '<=', date_end)])
            lead_count = 0
            for lead_id in lead_ids:
                lead_count += 1
            return lead_count
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            lead_ids = self.env['crm.lead'].sudo().search(
                [('marketing_id', '=', user_id.id),
                 ('create_date', '>=', date_start),
                 ('create_date', '<=', date_end),
                 ('old_lead_id', '=', False)
                 ])
            lead_count = 0
            for lead_id in lead_ids:
                lead_count += 1
            return lead_count
        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1

        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'department':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('department_id', '=', user_id.employee_id.department_id.id),
                     ('create_date', '>=', date_start),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'department':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('department_id', '=', user_id.employee_id.department_id.id),
                     ('create_date', '>=', date_start),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
            if self.okr_id.type_okr == 'company':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('create_date', '>=', date_start),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
        return lead_count

    def _count_lead_new(self, date_start, date_end, user_id):
        lead_count = 0
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            lead_ids = self.env['crm.lead'].sudo().search(
                [('user_id', '=', user_id.id),
                 ('date_open', '>=', date_start),
                 ('type_get_lead', '=', 'new'),
                 ('date_open', '<=', date_end)])
            lead_count = 0
            for lead_id in lead_ids:
                lead_count += 1
            return lead_count
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            lead_ids = self.env['crm.lead'].sudo().search(
                [('marketing_id', '=', user_id.id),
                 ('create_date', '>=', date_start),
                 ('type_get_lead', '=', 'new'),
                 ('create_date', '<=', date_end),
                 ('old_lead_id', '=', False)
                 ])
            lead_count = 0
            for lead_id in lead_ids:
                lead_count += 1
            return lead_count
        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1

        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'department':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('department_id', '=', user_id.employee_id.department_id.id),
                     ('create_date', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'department':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('department_id', '=', user_id.employee_id.department_id.id),
                     ('create_date', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
            if self.okr_id.type_okr == 'company':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('create_date', '>=', date_start),
                     ('type_get_lead', '=', 'new'),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
        return lead_count

    def _count_lead_old(self, date_start, date_end, user_id):
        lead_count = 0
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            lead_ids = self.env['crm.lead'].sudo().search(
                [('user_id', '=', user_id.id),
                 ('date_open', '>=', date_start),
                 ('type_get_lead', '=', 'old'),
                 ('date_open', '<=', date_end)])
            lead_count = 0
            for lead_id in lead_ids:
                lead_count += 1
            return lead_count
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            lead_ids = self.env['crm.lead'].sudo().search(
                [('marketing_id', '=', user_id.id),
                 ('create_date', '>=', date_start),
                 ('type_get_lead', '=', 'old'),
                 ('create_date', '<=', date_end),
                 ('old_lead_id', '=', False)
                 ])
            lead_count = 0
            for lead_id in lead_ids:
                lead_count += 1
            return lead_count
        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1

        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'department':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('department_id', '=', user_id.employee_id.department_id.id),
                     ('create_date', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'employee':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', user_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'team':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_open', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('date_open', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
            if self.okr_id.type_okr == 'department':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('department_id', '=', user_id.employee_id.department_id.id),
                     ('create_date', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
            if self.okr_id.type_okr == 'company':
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('create_date', '>=', date_start),
                     ('type_get_lead', '=', 'old'),
                     ('create_date', '<=', date_end)])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                return lead_count
        return lead_count

    def _sale_order_amount_reality(self, date_start, date_end, user_id):
        amount = 0
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            amount = 0
            move_ids = self.env['account.move'].sudo().search(
                [('state', '=', 'posted'),
                 ('invoice_user_id', '=', user_id.id),
                 ('invoice_date', '>=', date_start),
                 ('invoice_date', '<=', date_end)])
            for move_id in move_ids:
                amount += move_id.amount_for_sale1
            return amount
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            amount = 0
            move_ids = self.env['account.move'].sudo().search(
                [('state', '=', 'posted'),
                 '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                 ('invoice_date', '>=', date_start),
                 ('invoice_date', '<=', date_end)])
            for move_id in move_ids:
                sale_id = self.env['sale.order'].sudo().search(
                    [('name', '=', move_id.invoice_origin)])
                if sale_id.marketing_id == user_id:
                    amount += move_id.amount_for_sale1
            return amount
        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     ('invoice_user_id', '=', user_id.id),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '>', date_start - relativedelta(days=1)),
                     ('invoice_date', '<', date_end + relativedelta(days=1))])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount
            if self.okr_id.type_okr == 'team':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     ('invoice_user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '>=', date_start),
                     ('invoice_date', '<=', date_end)])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount
        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     ('invoice_user_id', '=', user_id.id),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '>=', date_start),
                     ('invoice_date', '<=', date_end)])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount
            if self.okr_id.type_okr == 'team':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     ('invoice_user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '>=', date_start),
                     ('invoice_date', '<=', date_end)])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount
            if self.okr_id.type_okr == 'department':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     ('invoice_user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('invoice_date', '>=', date_start),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '<=', date_end)])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount
        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'employee':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     ('invoice_user_id', '=', user_id.id),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '>=', date_start),
                     ('invoice_date', '<=', date_end)])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount
            if self.okr_id.type_okr == 'team':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     ('invoice_user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '>=', date_start),
                     ('invoice_date', '<=', date_end)])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount
            if self.okr_id.type_okr == 'department':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     ('invoice_user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('invoice_date', '>=', date_start),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '<=', date_end)])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount

            if self.okr_id.type_okr == 'company':
                amount = 0
                move_ids = self.env['account.move'].sudo().search(
                    [('state', '=', 'posted'),
                     '|',('sale_id', '!=', False),('pos_order_id', '!=', False),
                     ('invoice_date', '>=', date_start),
                     ('invoice_date', '<=', date_end)])
                for move_id in move_ids:
                    amount += move_id.amount_for_sale1
                return amount
        return amount

    def _sale_order_total(self, date_start, date_end, user_id):
        total = 0
        if user_id.has_group('vtg_security.group_vtg_employee_sale') or user_id.has_group(
                'vtg_security.group_vtg_employee_cashier'):
            sale_ids = self.env['sale.order'].sudo().search(
                [('state', 'in', ('sale', 'done')),
                 ('user_id', '=', user_id.id),
                 ('date_order', '>=', date_start),
                 ('date_order', '<=', date_end)])
            pos_ids = self.env['pos.order'].sudo().search(
                [('state', 'in', ('paid', 'done','invoiced')),
                 ('user_id', '=', user_id.id),
                 ('date_order', '>=', date_start),
                 ('date_order', '<=', date_end)])
            for sale_id in sale_ids:
                total += sale_id.amount_for_sale
            for pos_id in pos_ids:
                total += pos_id.amount_for_sale
            return total
        if user_id.has_group('vtg_security.group_vtg_employee_mkt'):
            total = 0
            # sale_ids = self.env['sale.order'].sudo().search(
            #     [('state', 'in', ('sale', 'done')),
            #      ('opportunity_id.marketing_id', '=', user_id.id),
            #      ('opportunity_id.create_date', '>=', date_start),
            #      ('opportunity_id.create_date', '<=', date_end)])
            sale_ids = self.env['sale.order'].sudo().search(
                [('state', 'in', ('sale', 'done')),
                 ('marketing_id', '=', user_id.id),
                 ('type_customer','=','new'),
                 ('date_order', '>=', date_start),
                 ('date_order', '<=', date_end)])
            pos_ids = self.env['pos.order'].sudo().search(
                [('state', 'in', ('paid', 'done','invoiced')),
                 ('marketing_id', '=', user_id.id),
                 ('type_customer', '=', 'new'),
                 ('date_order', '>=', date_start),
                 ('date_order', '<=', date_end)])
            for sale_id in sale_ids:
                total += sale_id.amount_for_sale
            for pos_id in pos_ids:
                total += pos_id.amount_for_sale
            return total
        if user_id.has_group('vtg_security.group_vtg_employee_team_sale'):
            if self.okr_id.type_okr == 'employee':
                sale_ids = self.env['sale.order'].sudo().search(
                    [('state', 'in', ('sale', 'done')),
                     ('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search(
                    [('state', 'in', ('paid', 'done','invoiced')),
                     ('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total
            if self.okr_id.type_okr == 'team':
                sale_ids = self.env['sale.order'].sudo().search(
                    [('state', 'in', ('sale', 'done')),
                     ('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search(
                    [('state', 'in', ('paid', 'done','invoiced')),
                     ('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total

        if user_id.has_group('vtg_security.group_vtg_director_sale'):
            if self.okr_id.type_okr == 'employee':
                sale_ids = self.env['sale.order'].sudo().search(
                    [('state', 'in', ('sale', 'done')),
                     ('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search(
                    [('state', 'in',  ('paid', 'done','invoiced')),
                     ('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total
            if self.okr_id.type_okr == 'team':
                sale_ids = self.env['sale.order'].sudo().search(
                    [('state', 'in', ('sale', 'done')),
                     ('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search(
                    [('state', 'in', ('paid', 'done','invoiced')),
                     ('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total
            if self.okr_id.type_okr == 'department':
                total = 0
                sale_ids = self.env['sale.order'].sudo().search(
                    [('state', 'in', ('sale', 'done')),
                     ('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search(
                    [('state', 'in', ('paid', 'done','invoiced')),
                     ('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total
        if user_id.has_group('vtg_security.group_vtg_director'):
            if self.okr_id.type_okr == 'employee':
                sale_ids = self.env['sale.order'].sudo().search(
                    [('state', 'in', ('sale', 'done')),
                     ('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search(
                    [('state', 'in', ('paid', 'done', 'invoiced')),
                     ('user_id', '=', user_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total
            if self.okr_id.type_okr == 'team':
                sale_ids = self.env['sale.order'].sudo().search(
                    [('state', 'in', ('sale', 'done')),
                     ('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search(
                    [('state', 'in', ('paid', 'done', 'invoiced')),
                     ('user_id.sale_team_id', '=', user_id.sale_team_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total
            if self.okr_id.type_okr == 'department':
                total = 0
                sale_ids = self.env['sale.order'].sudo().search(
                    [('state', 'in', ('sale', 'done')),
                     ('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search(
                    [('state', 'in', ('paid', 'done', 'invoiced')),
                     ('user_id.employee_id.department_id', '=', user_id.employee_id.department_id.id),
                     ('date_order', '>=', date_start),
                     ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total
            if self.okr_id.type_okr == 'company':
                total = 0
                sale_ids = self.env['sale.order'].sudo().search([
                    ('state', 'in', ('sale', 'done')),
                    ('date_order', '>=', date_start),
                    ('date_order', '<=', date_end)])
                pos_ids = self.env['pos.order'].sudo().search([
                    ('state', 'in', ('paid', 'done', 'invoiced')),
                    ('date_order', '>=', date_start),
                    ('date_order', '<=', date_end)])
                for sale_id in sale_ids:
                    total += sale_id.amount_for_sale
                for pos_id in pos_ids:
                    total += pos_id.amount_for_sale
                return total
        return total
