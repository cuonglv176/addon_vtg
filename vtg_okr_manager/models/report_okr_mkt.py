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

_logger = logging.getLogger(__name__)


class OKRReportMKT(models.Model):
    _name = 'dpt.okr.report.mkt'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(string='Tên')
    department_id = fields.Many2one('hr.department', string='Phòng')
    user_id = fields.Many2one('res.users', string='Nhân viên')
    date = fields.Date(string='Ngày')

    amount_kh = fields.Float(string='Doanh thu kế hoạch')
    amount_tt = fields.Float(string='Doanh thu thực tế')

    total_kh = fields.Float(string='Doanh số kế hoạch')
    total_tt = fields.Float(string='Doanh số thực tế')

    budget_kh = fields.Float(string='Chi tiêu kế hoạch')
    budget_tt = fields.Float(string='Chi tiêu thực tế')

    count_lead_kh = fields.Float(string='Lead kế hoạch')
    count_lead_tt = fields.Float(string='Lead thực tế')

    count_booking_kh = fields.Float(string='Booking kế hoạch')
    count_booking_tt = fields.Float(string='Booking thực tế')

    count_order_kh = fields.Float(string='Đơn hàng kế hoạch')
    count_order_tt = fields.Float(string='Đơn hàng thực tế')

    cost_lead_kh = fields.Float(string='Giá lead kế hoạch')
    cost_lead_tt = fields.Float(string='Giá lead thực tế')



    def _action_update_auto_cron(self, date_start, date_end):
        date_start = datetime.strptime(date_start, '%Y-%m-%d')
        date_end = datetime.strptime(date_end, '%Y-%m-%d')
        # booking_ids = self.env['crm.lead.booking'].search(
        #     [('create_date','>',date_start- relativedelta(days=1)),('create_date','<',date_start + relativedelta(days=1))])
        # for booking_id in booking_ids:
        #     booking_id._okr_report_mkt()
        # sale_ids = self.env['sale.order'].search([('create_date','>',date_start- relativedelta(days=1)),('create_date','<',date_start + relativedelta(days=1))])
        # _logger.info(">>>>>>>>>>>>>>>>>>>>>>>>")
        # _logger.info("sale_ids")
        # _logger.info(sale_ids)
        # for sale_id in sale_ids:
        #     sale_id._okr_report_mkt()
        # move_ids = self.env['account.move'].search([('invoice_date', '>', date_start - relativedelta(days=1)),
        #                                             ('invoice_date', '<', date_end + relativedelta(days=1))])
        # for move_id in move_ids:
        #     move_id._okr_report_mkt()

        # query ="""
        #     SELECT marketing_id, SUM(a.amount_total), invoice_date:: DATE
        #     FROM account_move a
        #     JOIN sale_order b on a.sale_id = b.id
        #     WHERE invoice_date >'03/01/2023' AND a.state = 'posted'
        #     GROUP BY b.marketing_id,invoice_date:: DATE
        #
        # """
        # self._cr.execute(query, ())
        # res_a = self._cr.fetchall()
        # for res in  res_a:
        #     mkt_id = self.env['dpt.okr.report.mkt'].sudo().search(
        #         [('user_id', '=', res[0]), ('date', '=', res[2])])
        #     user_id = self.env['res.users'].search([('id','=',res[0])])
        #     if not mkt_id:
        #         mkt_id = self.env['dpt.okr.report.mkt'].create({
        #             'name': user_id.name,
        #             'user_id': res[0],
        #             'department_id': user_id.employee_id.department_id.id,
        #             'date': res[2]
        #         })
        #     mkt_id.amount_tt = res[1]

        # query = """
        #             SELECT marketing_id, SUM(b.amount_total), date_order:: DATE
        #             FROM sale_order b
        #             WHERE date_order >'03/01/2023' AND state in ('done','sale')
        #             GROUP BY b.marketing_id,date_order:: DATE
        #
        #         """
        # self._cr.execute(query, ())
        # res_a = self._cr.fetchall()
        # for res in res_a:
        #     mkt_id = self.env['dpt.okr.report.mkt'].sudo().search(
        #         [('user_id', '=', res[0]), ('date', '=', res[2])])
        #     user_id = self.env['res.users'].search([('id', '=', res[0])])
        #     if not mkt_id:
        #         mkt_id = self.env['dpt.okr.report.mkt'].create({
        #             'name': user_id.name,
        #             'user_id': res[0],
        #             'department_id': user_id.employee_id.department_id.id,
        #             'date': res[2]
        #         })
        #     mkt_id.total_tt = res[1]

        # lead_ids = self.env['crm.lead'].search([('create_date', '>=', date_start),('create_date', '>=', date_end)])
        # _logger.info(">>>>>>>>>>>>>>>>>>>>>>>>")
        # _logger.info("lead_ids")
        # _logger.info(lead_ids)
        # for lead_id in lead_ids:
        #     lead_id._okr_report_mkt()

        # date = date_start
        # mkt_ids = self.env['dpt.okr.report.mkt'].sudo().search(
        #     [('date', '=', date.date())])
        # for mkt_id in mkt_ids:
        #     count_order_tt = self.env['sale.order'].sudo().search_count(
        #         [('date_order', '>', mkt_id.date - relativedelta(days=1)),
        #          ('date_order', '<', mkt_id.date + relativedelta(days=1)),
        #          ('opportunity_id.marketing_id.id', '=', mkt_id.user_id.id),
        #          ('type_customer', '=', 'new')])
        #     mkt_id.count_order_tt = count_order_tt
        #     total_tt = 0
        #     order_tt_ids = self.env['sale.order'].sudo().search(
        #         [('date_order', '>', mkt_id.date - relativedelta(days=1)),
        #          ('date_order', '<', mkt_id.date + relativedelta(days=1)),
        #          ('opportunity_id.marketing_id.id', '=',mkt_id.user_id.id),
        #          ('state', 'in', ('sale', 'done'))])
        #     for order_tt_id in order_tt_ids:
        #         total_tt += order_tt_id.amount_total
        #     mkt_id.total_tt = total_tt

        # sale_ids = self.env['sale.order'].sudo().search(
        #     [('date_order', '>', date_start - relativedelta(days=1)),('date_order', '<', date_end + relativedelta(days=1)),
        #      ('opportunity_id', '=', False),
        #      ('state', 'in', ('sale', 'done'))])
        # _logger.info("MMMMMMMMM")
        # _logger.info(len(sale_ids))
        # for sale_id in sale_ids:
        #     lead_id = self.env['crm.lead'].create({
        #         'name': sale_id.partner_id.name,
        #         'contact_name': sale_id.partner_id.name,
        #         'phone': sale_id.partner_id.phone,
        #         'source_id': sale_id.source_id.id,
        #         # 'user_id': sale_id.user_id.id,
        #         'marketing_id': sale_id.user_id.id,
        #         'department_id': sale_id.user_id.employee_id.department_id.id,
        #         'team_id': 12,
        #         'company_id': 1,
        #         'type': 'lead',
        #         'date_open': sale_id.date_order,
        #         'date_input': sale_id.create_date,
        #         'create_date': sale_id.create_date,
        #         'partner_id': sale_id.partner_id.id,
        #         'street': sale_id.address,
        #         'type_lead': 'resale',
        #     })
        #     sale_id.opportunity_id = lead_id
        #
        budget_ids = self.env['crm.kpi.mkt.budget'].search([('date', '>', date_start - relativedelta(days=1)),('date', '<', date_end + relativedelta(days=1))])
        # for budget_id in budget_ids:
        #     budget_id._okr_report_mkt()
        # kpi_ids = self.env['dpt.kpi.manager'].search([('okr_id.time_type','=','days'),('create_date', '>', date_start - relativedelta(days=1)),('create_date', '<', date_end + relativedelta(days=1))])
        # for kpi_id in kpi_ids:
        #     kpi_id._okr_report_mkt()


class SaleOrderOKR(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        sale_id = super(SaleOrderOKR, self).create(vals)
        # sale_id._okr_report_mkt()
        return sale_id

    def write(self, vals):
        for sale_id in self:
            res = super(SaleOrderOKR, self).write(vals)
            # sale_id._okr_report_mkt()
            return res

    def _okr_report_mkt(self):
        date_order = self.date_order or datetime.today()
        # mkt_id = self.env['dpt.okr.report.mkt'].sudo().search(
        #     [('user_id', '=', self.opportunity_id.marketing_id.id), ('date', '=', date_order.date())])
        # if not mkt_id:
        #     mkt_id = self.env['dpt.okr.report.mkt'].create({
        #         'name': self.opportunity_id.marketing_id.name,
        #         'user_id': self.opportunity_id.marketing_id.id,
        #         'department_id': self.opportunity_id.marketing_id.employee_id.department_id.id,
        #         'date': self.date_order.date(),
        #     })
        # count_order_tt = self.env['sale.order'].sudo().search_count(
        #     [('date_order', '>', mkt_id.date - relativedelta(days=1)),
        #      ('date_order', '<', mkt_id.date + relativedelta(days=1)),
        #      ('opportunity_id.marketing_id.id', '=', self.opportunity_id.marketing_id.id),
        #      ('type_customer', '=', 'new')])
        # mkt_id.count_order_tt = count_order_tt
        # total_tt = 0
        # order_tt_ids = self.env['sale.order'].sudo().search([('date_order', '>', mkt_id.date - relativedelta(days=1)),
        #                                                      ('date_order', '<', mkt_id.date + relativedelta(days=1)),
        #                                                      ('opportunity_id.marketing_id.id', '=',
        #                                                       self.opportunity_id.marketing_id.id),
        #                                                      ('state', 'in', ('sale', 'done'))])
        # for order_tt_id in order_tt_ids:
        #     total_tt += order_tt_id.amount_total
        # mkt_id.total_tt = total_tt

        okr_ids = self.env['dpt.okr.manager'].sudo().search(
            [('start_date', '<=', date_order.date()), ('end_date', '>=', date_order.date())])
        for okr_id in okr_ids:
            for kpi in okr_id.kpi_line_ids:
                if kpi.type == 'total':
                    total = kpi._sale_order_total(
                        okr_id.start_date,
                        okr_id.end_date, okr_id.employee_id.user_id)
                    kpi.result = total
                if kpi.type == 'order':
                    kpi.result = kpi._count_order(okr_id.start_date,
                                                  okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'order_cod':
                    kpi.result = kpi._count_order_cod(okr_id.start_date,
                                                  okr_id.end_date, okr_id.employee_id.user_id)
                if kpi.type == 'order_direct':
                    kpi.result = kpi._count_order_direct(okr_id.start_date,
                                                  okr_id.end_date, okr_id.employee_id.user_id)


            # okr_id._action_auto_update()


class AcountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        move_id = super(AcountMove, self).create(vals)
        # move_id._okr_report_mkt()
        return move_id

    def write(self, vals):
        for move_id in self:
            res = super(AcountMove, self).write(vals)
            move_id._okr_report_mkt()
            return res

    def _okr_report_mkt(self):
        date = self.invoice_date or datetime.today()
        # mkt_id = self.env['dpt.okr.report.mkt'].sudo().search(
        #     [('user_id', '=', self.sale_id.marketing_id.id), ('date', '=', date)])
        # if not mkt_id:
        #     mkt_id = self.env['dpt.okr.report.mkt'].create({
        #         'name': self.sale_id.marketing_id.name,
        #         'user_id': self.sale_id.marketing_id.id,
        #         'department_id': self.sale_id.marketing_id.employee_id.department_id.id,
        #         'date': date,
        #     })
        # move_ids = self.env['account.move'].sudo().search(
        #     [('state', '=', 'posted'),
        #      ('invoice_date', '=', date),
        #      ('sale_id.marketing_id', '=', self.sale_id.marketing_id.id),
        #      ])
        # amount_tt = 0
        # for move_id in move_ids:
        #     amount_tt += move_id.amount_total
        # mkt_id.amount_tt = amount_tt

        # okr_ids = self.env['dpt.okr.manager'].sudo().search(
        #     [('start_date', '<=', date), ('end_date', '>=', date)])
        # for okr_id in okr_ids:
        #     okr_id._action_auto_update()

        okr_ids = self.env['dpt.okr.manager'].sudo().search(
            [('start_date', '<=', date), ('end_date', '>=', date)])
        for okr_id in okr_ids:
            for kpi in okr_id.kpi_line_ids:
                if kpi.type == 'amount':
                    amount_total = kpi._sale_order_amount_reality(
                        okr_id.start_date,
                        okr_id.end_date, okr_id.employee_id.user_id)
                    kpi.result = amount_total


class CrmLeadOKR(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        lead_id = super(CrmLeadOKR, self).create(vals)
        # lead_id._okr_report_mkt()
        return lead_id

    def write(self, vals):
        for lead_id in self:
            res = super(CrmLeadOKR, self).write(vals)
            lead_id._okr_report_mkt()
            return res

    def _okr_report_mkt(self):
        date = self.create_date or datetime.now()
        # mkt_id = self.env['dpt.okr.report.mkt'].sudo().search(
        #     [('user_id', '=', self.marketing_id.id), ('date', '=', date.date())])
        # if not mkt_id:
        #     mkt_id = self.env['dpt.okr.report.mkt'].create({
        #         'name': self.marketing_id.name,
        #         'user_id': self.marketing_id.id,
        #         'department_id': self.marketing_id.employee_id.department_id.id,
        #         'date': date.date(),
        #     })
        # count_lead_tt = self.env['crm.lead'].sudo().search_count(
        #     [('create_date', '>', mkt_id.date - relativedelta(days=1)),
        #      ('create_date', '<', mkt_id.date + relativedelta(days=1)),
        #      ('marketing_id', '=', self.marketing_id.id),
        #      ])
        # mkt_id.count_lead_tt = count_lead_tt
        # okr_ids = self.env['dpt.okr.manager'].sudo().search(
        #     [('start_date', '<=', date.date()), ('end_date', '>=', date.date())])
        # for okr_id in okr_ids:
        #     okr_id._action_auto_update()
        okr_ids = self.env['dpt.okr.manager'].sudo().search(
            [('start_date', '<=', date.date()), ('end_date', '>=', date.date())])
        for okr_id in okr_ids:
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


class BookingOKR(models.Model):
    _inherit = 'crm.lead.booking'

    @api.model
    def create(self, vals):
        booking_id = super(BookingOKR, self).create(vals)
        # booking_id._okr_report_mkt()
        return booking_id

    def write(self, vals):
        for booking_id in self:
            res = super(BookingOKR, self).write(vals)
            booking_id._okr_report_mkt()
            return res

    def _okr_report_mkt(self):
        date = self.date_sent or datetime.now()
        # mkt_id = self.env['dpt.okr.report.mkt'].sudo().search(
        #     [('user_id', '=', self.lead_id.marketing_id.id), ('date', '=', date.date())])
        # if not mkt_id:
        #     mkt_id = self.env['dpt.okr.report.mkt'].create({
        #         'name': self.lead_id.marketing_id.name,
        #         'user_id': self.lead_id.marketing_id.id,
        #         'department_id': self.lead_id.marketing_id.employee_id.department_id.id,
        #         'date': date.date(),
        #     })
        # count_booking_tt = self.env['crm.lead.booking'].sudo().search_count(
        #     [('date_sent', '>', mkt_id.date - relativedelta(days=1)),
        #      ('date_sent', '<', mkt_id.date + relativedelta(days=1)),
        #      ('lead_id.marketing_id', '<', self.lead_id.marketing_id.id)
        #      ])
        # mkt_id.count_booking_tt = count_booking_tt
        okr_ids = self.env['dpt.okr.manager'].sudo().search(
            [('start_date', '<=', date.date()), ('end_date', '>=', date.date())])
        for okr_id in okr_ids:
            # okr_id._action_auto_update()
            for kpi in okr_id.kpi_line_ids:
                if kpi.type == 'booking':
                    kpi.result = kpi._count_booking(okr_id.start_date,
                                                okr_id.end_date, okr_id.employee_id.user_id)


class BudgetOKR(models.Model):
    _inherit = 'crm.kpi.mkt.budget'

    @api.model
    def create(self, vals):
        budget_id = super(BudgetOKR, self).create(vals)
        budget_id._okr_report_mkt()
        return budget_id

    def write(self, vals):
        for budget_id in self:
            res = super(BudgetOKR, self).write(vals)
            budget_id._okr_report_mkt()
            return res

    def _okr_report_mkt(self):
        date = self.date or datetime.today()
        # mkt_id = self.env['dpt.okr.report.mkt'].sudo().search(
        #     [('user_id', '=', self.user_id.id), ('date', '=', date)])
        # if not mkt_id:
        #     mkt_id = self.env['dpt.okr.report.mkt'].create({
        #         'name': self.user_id.name,
        #         'user_id': self.user_id.id,
        #         'department_id': self.user_id.employee_id.department_id.id,
        #         'date': date,
        #     })
        # budget_tt_ids = self.env['crm.kpi.mkt.budget'].sudo().search(
        #     [('date', '>', mkt_id.date - relativedelta(days=1)),
        #      ('date', '<', mkt_id.date + relativedelta(days=1)),
        #      ('user_id', '<', self.user_id.id)
        #      ])
        # budget_tt = 0
        # for budget_tt_id in budget_tt_ids:
        #     budget_tt += budget_tt_id.budget
        # mkt_id.budget_tt = budget_tt
        okr_ids = self.env['dpt.okr.manager'].sudo().search(
            [('start_date', '<=', date), ('end_date', '>=', date)])
        for okr_id in okr_ids:
            # okr_id._action_auto_update()
            for kpi in okr_id.kpi_line_ids:
                if kpi.type == 'cost':
                    kpi.result = kpi._sum_cost(okr_id.start_date,
                                           okr_id.end_date, okr_id.employee_id.user_id)


class OKRKPIManager(models.Model):
    _inherit = 'dpt.kpi.manager'

    @api.model
    def create(self, vals):
        kpi_id = super(OKRKPIManager, self).create(vals)
        if kpi_id.okr_id.time_type == 'days':
            kpi_id._okr_report_mkt()
        return kpi_id

    def write(self, vals):
        for kpi_id in self:
            res = super(OKRKPIManager, self).write(vals)
            if kpi_id.okr_id.time_type == 'days':
                kpi_id._okr_report_mkt()
            return res

    def _okr_report_mkt(self):
        date = self.okr_id.start_date or datetime.today()
        mkt_id = self.env['dpt.okr.report.mkt'].sudo().search(
            [('user_id', '=', self.okr_id.employee_id.user_id.id), ('date', '=', date)])
        if not mkt_id:
            mkt_id = self.env['dpt.okr.report.mkt'].create({
                'name': self.okr_id.employee_id.name,
                'user_id': self.okr_id.employee_id.user_id.id,
                'department_id': self.okr_id.employee_id.department_id.id,
                'date': date,
            })
        if self.type == 'lead':
            mkt_id.count_lead_kh = self.value
        if self.type == 'amount':
            mkt_id.amount_kh = self.value
        if self.type == 'cost':
            mkt_id.budget_kh = self.value
        if self.type == 'booking':
            mkt_id.count_booking_kh = self.value
        if self.type == 'order':
            mkt_id.count_order_kh = self.value
        if self.type == 'total':
            mkt_id.total_kh = self.value
