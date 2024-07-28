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
import logging

_logger = logging.getLogger(__name__)


class CrmLeadBooking(models.Model):
    _inherit = 'crm.lead.booking'

    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh', compute="depends_channel_id", store=True,track_visibility='onchange')

    @api.depends('source_id')
    def depends_channel_id(self):
        for s in self:
            if s.source_id:
                s.channel_id = s.source_id.channel_id


# class CRMLEADINHERIT(models.Model):
#     _inherit = 'crm.lead'
#
#     def write(self, vals):
#         for lead_id in self:
#             res = super(CRMLEADINHERIT, self).write(vals)
#             date_open = lead_id.date_open or lead_id.create_date or datetime.now()
#             kpi_sale_ids = self.env['crm.kpi.sale'].sudo().search(
#                 [('user_id', '=', lead_id.user_id.id), ('date_start', '<', date_open),
#                  ('date_end', '>', date_open - relativedelta(hours=23))])
#             for kpi_sale_id in kpi_sale_ids:
#                 query = """SELECT COUNT(*) lead_count
#                             FROM crm_lead
#                             WHERE date_open > %s
#                             AND date_open < %s
#                             AND stage_id not in (2,15,16)
#                             AND user_id = %s """
#                 self._cr.execute(query, (kpi_sale_id.date_start, kpi_sale_id.date_end, kpi_sale_id.user_id.id))
#                 lead_counts = self._cr.fetchone()
#                 kpi_sale_id.lead_count = lead_counts[0]
#                 if kpi_sale_id.lead_count > 0:
#                     kpi_sale_id.amount_per_lead = kpi_sale_id.amount_total_khm / kpi_sale_id.lead_count
#                 if kpi_sale_id.lead_count_kpi > 0:
#                     kpi_sale_id.lead_count_percent = (kpi_sale_id.lead_count / kpi_sale_id.lead_count_kpi) * 100
#             return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh', compute="depends_channel_id", store=True,track_visibility='onchange')

    @api.depends('source_id')
    def depends_channel_id(self):
        for s in self:
            if s.source_id:
                s.channel_id = s.source_id.channel_id


#     @api.model
#     def create(self, vals):
#         sale_id = super(SaleOrder, self).create(vals)
#         date_order = sale_id.date_order or sale_id.create_date
#         kpi_sale_ids = self.env['crm.kpi.sale'].sudo().search(
#             [('user_id', '=', sale_id.user_id.id), ('date_start', '<', date_order),
#              ('date_end', '>', date_order - relativedelta(hours=23))])
#         for kpi_sale_id in kpi_sale_ids:
#             kpi_sale_id._sale_order_add(kpi_sale_id.date_start, kpi_sale_id.date_end, kpi_sale_id.user_id)
#             # UPDATE KPI
#             amount_total, amount_total_khm, amount_total_khc, amount_total_khtt = kpi_sale_id._sale_order_amount_reality(
#                 kpi_sale_id.date_start,
#                 kpi_sale_id.date_end + relativedelta(days=1),
#                 kpi_sale_id.user_id)
#             kpi_sale_id.amount_total = amount_total
#             kpi_sale_id.amount_total_khc = amount_total_khc
#             kpi_sale_id.amount_total_khm = amount_total_khm
#             kpi_sale_id.amount_total_khtt = amount_total_khtt
#             if kpi_sale_id.lead_count > 0:
#                 kpi_sale_id.amount_per_lead = kpi_sale_id.amount_total_khm / kpi_sale_id.lead_count
#             if kpi_sale_id.amount_total_kpi > 0:
#                 kpi_sale_id.amount_total_percent = (kpi_sale_id.amount_total / kpi_sale_id.amount_total_kpi) * 100
#             # UPDATE LINE
#             for line in kpi_sale_id.line_ids:
#                 amount, amount_khm, amount_khc, amount_khtt = kpi_sale_id._sale_order_amount_reality(
#                     line.date_start,
#                     line.date_end + relativedelta(days=1),
#                     line.user_id)
#                 line.amount = amount
#                 line.amount_khc = amount_khc
#                 line.amount_khm = amount_khm
#                 line.amount_khtt = amount_khtt
#             # UPDATE LINE DAY
#             for line in kpi_sale_id.line_day_ids:
#                 amount, amount_khm, amount_khc, amount_khtt = kpi_sale_id._sale_order_amount_reality(
#                     line.date,
#                     line.date + relativedelta(hours=23),
#                     line.user_id)
#                 line.amount = amount
#                 line.amount_reality = amount
#                 line.amount_khc = amount_khc
#                 line.amount_khm = amount_khm
#                 line.amount_khtt = amount_khtt
#         return sale_id
#
#     def write(self, vals):
#         for sale_id in self:
#             res = super(SaleOrder, self).write(vals)
#             query = """DELETE FROM crm_kpi_sale_line_sale_order
#                     WHERE order_id in (SELECT id FROM sale_order WHERE state = 'cancel') """
#             self._cr.execute(query)
#
#             query2 = """DELETE FROM crm_kpi_sale_line_sale_order2
#                                 WHERE order_id in (SELECT id FROM sale_order WHERE state = 'cancel') """
#             self._cr.execute(query2)
#
#
#             date_order = sale_id.date_order or sale_id.create_date
#             kpi_sale_ids = self.env['crm.kpi.sale'].sudo().search(
#                 [('user_id', '=', sale_id.user_id.id), ('date_start', '<', date_order),
#                  ('date_end', '>', date_order - relativedelta(hours=23)), ('date_end', '>', '2012-12-31')])
#             for kpi_sale_id in kpi_sale_ids:
#                 kpi_sale_id._sale_order_add(kpi_sale_id.date_start, kpi_sale_id.date_end, kpi_sale_id.user_id)
#                 # UPDATE KPI
#                 amount_total, amount_total_khm, amount_total_khc, amount_total_khtt = kpi_sale_id._sale_order_amount_reality(
#                     kpi_sale_id.date_start,
#                     kpi_sale_id.date_end + relativedelta(days=1),
#                     kpi_sale_id.user_id)
#                 _logger.info(">>>>>>>>>>>>>>>>>>>>>>>>")
#                 _logger.info(amount_total)
#                 kpi_sale_id.amount_total = amount_total
#                 kpi_sale_id.amount_total_khc = amount_total_khc
#                 kpi_sale_id.amount_total_khm = amount_total_khm
#                 kpi_sale_id.amount_total_khtt = amount_total_khtt
#                 if kpi_sale_id.lead_count > 0:
#                     kpi_sale_id.amount_per_lead = kpi_sale_id.amount_total_khm / kpi_sale_id.lead_count
#                 if kpi_sale_id.amount_total_kpi > 0:
#                     kpi_sale_id.amount_total_percent = (kpi_sale_id.amount_total / kpi_sale_id.amount_total_kpi) * 100
#                 # UPDATE LINE
#                 for line in kpi_sale_id.line_ids:
#                     amount, amount_khm, amount_khc, amount_khtt = kpi_sale_id._sale_order_amount_reality(
#                         line.date_start,
#                         line.date_end + relativedelta(days=1),
#                         line.user_id)
#                     line.amount = amount
#                     line.amount_khc = amount_khc
#                     line.amount_khm = amount_khm
#                     line.amount_khtt = amount_khtt
#                 # UPDATE LINE DAY
#                 for line in kpi_sale_id.line_day_ids:
#                     amount, amount_khm, amount_khc, amount_khtt = kpi_sale_id._sale_order_amount_reality(
#                         line.date,
#                         line.date + relativedelta(hours=23),
#                         line.user_id)
#                     line.amount = amount
#                     line.amount_reality = amount
#                     line.amount_khc = amount_khc
#                     line.amount_khm = amount_khm
#                     line.amount_khtt = amount_khtt
#             return res


class CRMKpisale(models.Model):
    _name = 'crm.kpi.sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    @api.model
    def _get_default_code(self):
        return self.env["ir.sequence"].next_by_code("crm.kpi.sale")

    name = fields.Char(string='Tên KPI', track_visibility='onchange')
    line_ids = fields.One2many('crm.kpi.sale.line', 'kpi_id', string='KPI theo tuần')
    line_day_ids = fields.One2many('crm.kpi.sale.line.day', 'kpi_id', string='Kết quả theo ngày')
    line_sale_order_ids = fields.One2many('crm.kpi.sale.line.sale.order', 'kpi_id', string='Kết quả theo đơn hàng')
    line_sale_order2_ids = fields.One2many('crm.kpi.sale.line.sale.order2', 'kpi_id', string='Kết quả theo đơn hàng')
    date_start = fields.Date(string="Thời gian bắt đầu", required=True)
    date_end = fields.Date(string="Thời gian kết thúc", required=True)
    team_id = fields.Many2one('crm.team', string="Nhóm bán hàng", required=True)
    user_id = fields.Many2one('res.users', string="Nhân viên kinh doanh", required=True)
    # "LEAD"
    lead_count_kpi = fields.Integer(string='Lead kế hoạch')
    lead_count_kpi_per_day = fields.Integer(string='Lead dự kiến trên ngày')
    lead_count = fields.Integer(string='Số lead thực tế')
    lead_count_percent = fields.Integer(string='Tỉ lệ đạt')
    # "DOANH THU"
    currency_id = fields.Many2one('res.currency', string='tiền tệ', default=23)
    amount_total_kpi = fields.Float(string='Doanh thu kế hoạch')
    amount_total = fields.Float(string='Doanh thu thực tế')
    amount_total_khm = fields.Float(string='Doanh thu thực tế KHM')
    amount_total_khc = fields.Float(string='Doanh thu thực tế KHC')
    amount_total_khtt = fields.Float(string='Doanh thu thực tế KHTT')
    amount_total_percent = fields.Float(string='Tỉ lệ đạt')
    sale_ids = fields.Many2many('sale.order', string='Đơn hàng')
    # "GIÁ LEAD"
    amount_per_lead = fields.Float(string='Doanh thu / Lead')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Xác nhận'),
        ('cancel', 'Từ chối')
    ], string='Trạng thái', default='draft', track_visibility='onchange')
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

    @api.onchange('amount_total', 'lead_count')
    def onchange_amount_per_lead(self):
        if self.amount_total > 0 and self.lead_count > 0:
            self.amount_per_lead = self.amount_total_khm / self.lead_count

    @api.onchange('amount_total_kpi', 'date_start', 'date_end')
    def onchange_amount_total_per_week(self):
        if self.amount_total_kpi:
            amount_total_kpi_per_week = self.amount_total_kpi / len(self.line_ids)
            for line in self.line_ids:
                if line.amount_target == 0:
                    line.amount_target = amount_total_kpi_per_week

    @api.onchange('lead_count_kpi', 'date_start', 'date_end')
    def onchange_lead_count_per_day(self):
        if self.lead_count_kpi:
            day_start = self.date_start.day
            day_end = self.date_end.day
            self.lead_count_kpi_per_day = self.lead_count_kpi / (day_end - day_start)
            lead_count_kpi_per_week = self.lead_count_kpi / len(self.line_ids)
            for line in self.line_ids:
                if line.qty_lead_target == 0:
                    line.qty_lead_target = lead_count_kpi_per_week

    @api.onchange('date_start', 'date_end', 'user_id')
    def _onchange_amount_total(self):
        for s in self:
            if s.date_start and s.date_end:
                # sale_ids = self.env['sale.order'].sudo().search(
                #     [('user_id', '=', s.user_id.id), ('date_order', '>=', s.date_start),
                #      ('date_order', '<=', s.date_end), ('state', 'in', ('draft', 'sale', 'done'))])
                # amount_total = 0
                # for sale_id in sale_ids:
                #     amount_total += sale_id.amount_total
                amount_reality, amount_khm_reality, amount_khc_reality, amount_khtt_reality = self._sale_order_amount_reality(
                    s.date_start,
                    s.date_end + relativedelta(days=1),
                    s.user_id)
                s.amount_total = amount_reality
                s.amount_total_khc = amount_khc_reality
                s.amount_total_khm = amount_khm_reality
                s.amount_total_khtt = amount_khtt_reality

    @api.onchange('date_start', 'date_end', 'user_id', 'amount_total_kpi')
    def _onchange_amount_total_percent(self):
        for s in self:
            if s.date_start and s.date_end:
                # sale_ids = self.env['sale.order'].sudo().search(
                #     [('user_id', '=', s.user_id.id), ('date_order', '>=', s.date_start),
                #      ('date_order', '<=', s.date_end), ('state', 'in', ('draft', 'sale', 'done'))])
                # amount_total = 0
                # for sale_id in sale_ids:
                #     amount_total += sale_id.amount_total
                amount_reality, amount_khm_reality, amount_khc_reality, amount_khtt_reality = self._sale_order_amount_reality(
                    s.date_start,
                    s.date_end + relativedelta(days=1),
                    s.user_id)
                if s.amount_total_kpi > 0:
                    s.amount_total_percent = (amount_reality / s.amount_total_kpi) * 100
                else:
                    s.amount_total_percent = 0

    @api.onchange('date_start', 'date_end', 'user_id')
    def _onchange_lead_count(self):
        for s in self:
            if s.date_start and s.date_end:
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', s.user_id.id), ('date_open', '>=', s.date_start),
                     ('date_open', '<=', s.date_end), ('stage_id', 'not in', (2, 15, 16))])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                s.lead_count = lead_count

    @api.onchange('date_start', 'date_end', 'user_id', 'lead_count', 'lead_count_kpi')
    def _onchange_lead_count_percent(self):
        for s in self:
            if s.date_start and s.date_end:
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', s.user_id.id), ('date_open', '>=', s.date_start),
                     ('date_open', '<=', s.date_end), ('stage_id', 'not in', (2, 15, 16))])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                s.lead_count = lead_count
                if s.lead_count_kpi > 0:
                    s.lead_count_percent = (lead_count / s.lead_count_kpi) * 100
                else:
                    s.lead_count_percent = 0

    def _get_nextcall_monthly_leave(self, month):
        date_1 = date.today()
        start_date = datetime(date_1.year, month, 1)
        end_date = datetime(date_1.year, month, calendar.mdays[month])
        return start_date, end_date

    @api.onchange('month', 'user_id')
    def onchange_state_end_date(self):
        if self.month:
            self.date_start, self.date_end = self._get_nextcall_monthly_leave(int(self.month))
            if self.line_day_ids:
                self.line_day_ids = None
            if self.line_ids:
                self.line_ids = None
            if self.line_sale_order_ids:
                self.line_sale_order_ids = None
            if self.line_sale_order2_ids:
                self.line_sale_order2_ids = None
            self._sale_order_add(self.date_start, self.date_end, self.user_id)
            self.onchange_state_end_date_create_line(self.date_start, self.date_end)
            day = (self.date_end - self.date_start)
            if day != 0:
                vals_add = []
                for n in range(int(day.days) + 1):
                    qty_lead = self._count_lead(self.date_start + relativedelta(days=n),
                                                self.date_start + relativedelta(days=n), self.user_id)

                    amount, amount_khc, amount_khm = self._sale_order_amount(self.date_start + relativedelta(days=n),
                                                                             self.date_start + relativedelta(days=n),
                                                                             self.user_id)
                    amount_reality, amount_khm_reality, amount_khc_reality, amount_khtt_reality = self._sale_order_amount_reality(
                        self.date_start + relativedelta(days=n),
                        self.date_start + relativedelta(days=n + 1),
                        self.user_id)

                    vals = {
                        'kpi_id': self.id,
                        'date': self.date_start + relativedelta(days=n),
                        'qty_lead': qty_lead,
                        'user_id': self.user_id.id,
                        'amount': amount,
                        'amount_reality': amount_reality,
                        'amount_khc': amount_khc_reality,
                        'amount_khm': amount_khm_reality,
                        'amount_khtt': amount_khtt_reality,
                    }
                    vals_add.append((0, 0, vals))
                self.line_day_ids = vals_add

    def _count_lead(self, date_start, date_end, user_id):
        lead_ids = self.env['crm.lead'].sudo().search(
            [('user_id', '=', user_id.id), ('date_open', '>=', date_start),
             ('date_open', '<=', date_end), ('stage_id', 'not in', (2, 15, 16))])
        lead_count = 0
        for lead_id in lead_ids:
            lead_count += 1
        return lead_count

    def _sale_order_add(self, date_start, date_end, user_id):
        if self.sale_ids:
            self.sale_ids = None
        acount_moves = self.env['account.move'].sudo().search(
            [('invoice_user_id', '=', user_id.id), ('invoice_date', '>=', date_start),
             ('invoice_date', '<=', date_end), ('state', '=', 'posted')])
        sale_list = []
        for acount_id in acount_moves:
            sale_ids = self.env['sale.order'].sudo().search(
                [('name', '=', acount_id.invoice_origin)])
            for sale in sale_ids:
                sale_list.append(sale.id)
        sale_o_ids = self.env['sale.order'].sudo().search(
            [('user_id', '=', user_id.id), ('date_order', '>=', date_start),
             ('date_order', '<=', date_end), ('state', 'in', ('draft', 'sale', 'done')), ('id', 'not in', sale_list)])
        for sale in sale_o_ids:
            sale_list.append(sale.id)
        list_set = list(set(sale_list))
        _logger.info(list_set)
        sale_u_ids = self.env['sale.order'].sudo().search([('id', 'in', list_set)])
        for sale in sale_u_ids:
            self._add_line_sale_order(sale)
        self.sale_ids = [(6, 0, sale_list)]

    def _add_line_sale_order(self, sale_id):
        line_sale_order_id = self.env['crm.kpi.sale.line.sale.order'].sudo().search([('order_id', '=', sale_id.id),
                                                                                     ('kpi_id', '=', self.id)])
        line_sale_order2_id = self.env['crm.kpi.sale.line.sale.order2'].sudo().search([('order_id', '=', sale_id.id),
                                                                                       ('kpi_id', '=', self.id)])
        amount_total, amount_khm, amount_khc, amount_khtt = self._sale_order_amount_reality_by_order(sale_id)
        invoice_id = self.env['account.move'].sudo().search(
            [('invoice_origin', '=', sale_id.name), ('state', '=', 'posted')], limit=1)
        if line_sale_order_id:
            line_sale_order_id.write({
                'date': sale_id.date_order,
                'date_invoice': invoice_id.invoice_date,
                'date_fill': invoice_id.invoice_date or sale_id.date_order,
                'user_id': sale_id.user_id.id,
                'team_id': sale_id.team_id.id,
                'amount': sale_id.amount_total,
                'amount_reality': amount_total or 0,
            })
        else:
            self.env['crm.kpi.sale.line.sale.order'].sudo().create({
                'date': sale_id.date_order,
                'date_invoice': invoice_id.invoice_date,
                'date_fill': invoice_id.invoice_date or sale_id.date_order,
                'user_id': sale_id.user_id.id,
                'team_id': sale_id.team_id.id,
                'amount': sale_id.amount_total,
                'amount_reality': amount_total or 0,
                'kpi_id': self.id,
                'order_id': sale_id.id,
            })

        if line_sale_order2_id:
            line_sale_order2_id.write({
                'date': sale_id.date_order,
                'date_invoice': invoice_id.invoice_date,
                'date_fill': invoice_id.invoice_date or sale_id.date_order,
                'user_id': sale_id.user_id.id,
                'team_id': sale_id.team_id.id,
                'amount': sale_id.amount_total,
                'amount_reality': amount_total or 0,
            })
        else:
            self.env['crm.kpi.sale.line.sale.order2'].sudo().create({
                'date': sale_id.date_order,
                'date_invoice': invoice_id.invoice_date,
                'date_fill': invoice_id.invoice_date or sale_id.date_order,
                'user_id': sale_id.user_id.id,
                'team_id': sale_id.team_id.id,
                'amount': sale_id.amount_total,
                'amount_reality': amount_total or 0,
                'kpi_id': self.id,
                'order_id': sale_id.id,
            })

    def _sale_order_amount_reality_by_order(self, sale_id):
        # query = """
        #     SELECT SUM(a.price_total),d.type_customer
        #             FROM sale_order_line a
        #             JOIN product_product b on a.product_id = b.id
        #             JOIN product_template c on b.product_tmpl_id = c.id
        #             JOIN sale_order d on a.order_id = d.id
        #             WHERE c.categ_id in (1,2,3,4)
        #             AND d."state" in ('done','sale')
        #             AND d."status_transfer" not in ('return')
        #             AND d.type_order = 'cod'
        #             AND d.id = %s
        #             GROUP BY d.type_customer
        #     UNION ALL
        #             SELECT SUM(a.price_total),d.type_customer
        #             FROM sale_order_line a
        #             JOIN product_product b on a.product_id = b.id
        #             JOIN product_template c on b.product_tmpl_id = c.id
        #             JOIN sale_order d on a.order_id = d.id
        #             WHERE c.categ_id in (1,2,3,4)
        #             AND d."state" in ('done','sale')
        #             AND d.type_order = 'ship'
        #             AND d.id = %s
        #             GROUP BY d.type_customer
        #     UNION ALL
        #             SELECT SUM(a.price_total),d.type_customer
        #             FROM sale_order_line a
        #             JOIN product_product b on a.product_id = b.id
        #             JOIN product_template c on b.product_tmpl_id = c.id
        #             JOIN sale_order d on a.order_id = d.id
        #             WHERE (c.categ_id in (1,2) or a.user_id = d.user_id)
        #             AND d."state" in ('done','sale')
        #             AND d.type_order = 'direct'
        #             AND d.id = %s
        #             GROUP BY d.type_customer
        # """
        query = """
            SELECT SUM(a.price_total),d.type_customer
                FROM sale_order_line a 
                JOIN product_product b on a.product_id = b.id 
                JOIN product_template c on b.product_tmpl_id = c.id
                JOIN sale_order d on a.order_id = d.id
                WHERE c.categ_id in (1,2,3,4)
                AND d."state" in ('done','sale')
                AND d.type_order = 'cod'
                AND d.id = %s
                AND d.name in (SELECT invoice_origin FROM account_move WHERE "state" = 'posted')
                GROUP BY d.type_customer
            UNION ALL
                SELECT SUM(a.price_total),d.type_customer
                FROM sale_order_line a 
                JOIN product_product b on a.product_id = b.id 
                JOIN product_template c on b.product_tmpl_id = c.id
                JOIN sale_order d on a.order_id = d.id
                WHERE c.categ_id in (1,2,3,4)
                AND d."state" in ('done','sale')
                AND d.type_order = 'ship'
                AND d.id = %s
                AND d.name in (SELECT invoice_origin FROM account_move WHERE "state" = 'posted')
                GROUP BY d.type_customer
            UNION ALL
                SELECT SUM(a.price_total),d.type_customer
                FROM sale_order_line a 
                JOIN product_product b on a.product_id = b.id 
                JOIN product_template c on b.product_tmpl_id = c.id
                JOIN sale_order d on a.order_id = d.id
                WHERE (c.categ_id in (1,2) or a.user_id = d.user_id)
                AND d."state" in ('done','sale')
                AND d.type_order = 'direct'
                AND d.id = %s
                AND d.name in (SELECT invoice_origin FROM account_move WHERE "state" = 'posted')
                GROUP BY d.type_customer
        """
        self._cr.execute(query, (
            sale_id.id or 0, sale_id.id or 0, sale_id.id or 0))
        res = self._cr.fetchall()
        amount_khm = 0
        amount_khc = 0
        amount_khtt = 0
        for r in res:
            if r[1] == 'new':
                if r[0]:
                    amount_khm += r[0]
            if r[1] == 'old':
                if r[0]:
                    amount_khc += r[0]
            if r[1] == 'find':
                if r[0]:
                    amount_khtt += r[0]
        amount_total = amount_khm + amount_khc + amount_khtt
        return amount_total, amount_khm, amount_khc, amount_khtt

    def _sale_order_amount(self, date_start, date_end, user_id):
        sale_ids = self.env['sale.order'].sudo().search(
            [('user_id', '=', user_id.id),
             ('date_order', '>=', date_start),
             ('date_order', '<=', date_end),
             ('state', 'in', ('sale', 'done'))])
        amount_total = 0
        for sale_id in sale_ids:
            amount_total += sale_id.amount_total

        sale_khc_ids = self.env['sale.order'].sudo().search(
            [('user_id', '=', user_id.id),
             ('date_order', '>=', date_start),
             ('date_order', '<=', date_end),
             ('type_customer', '=', 'old'),
             ('state', 'in', ('sale', 'done'))])
        amount_khc = 0
        for sale_id in sale_khc_ids:
            amount_khc += sale_id.amount_total

        sale_khm_ids = self.env['sale.order'].sudo().search(
            [('user_id', '=', user_id.id),
             ('date_order', '>=', date_start),
             ('date_order', '<=', date_end),
             ('type_customer', '=', 'new'),
             ('state', 'in', ('sale', 'done'))])
        amount_khm = 0
        for sale_id in sale_khm_ids:
            amount_khm += sale_id.amount_total
        return amount_total, amount_khc, amount_khm

    def _sale_order_amount_reality(self, date_start, date_end, user_id):
        query = """
            SELECT SUM(a.price_total),d.type_customer
                    FROM sale_order_line a
                    JOIN product_product b on a.product_id = b.id
                    JOIN product_template c on b.product_tmpl_id = c.id
                    JOIN sale_order d on a.order_id = d.id
                    WHERE c.categ_id in (1,2,3,4)
                    AND d."state" in ('done','sale')
                    AND d.type_order = 'cod'
                    AND d.name in (SELECT invoice_origin FROM account_move e
                    WHERE "state" = 'posted'
                    AND e.invoice_date >= %s
                    AND e.invoice_date < %s)
                    AND d.user_id = %s
                    GROUP BY d.type_customer
            UNION ALL
                    SELECT SUM(a.price_total),d.type_customer
                    FROM sale_order_line a
                    JOIN product_product b on a.product_id = b.id
                    JOIN product_template c on b.product_tmpl_id = c.id
                    JOIN sale_order d on a.order_id = d.id
                    WHERE c.categ_id in (1,2,3,4)
                    AND d."state" in ('done','sale')
                    AND d.type_order = 'ship'
                    AND d.name in (SELECT invoice_origin FROM account_move e
                    WHERE "state" = 'posted'
                    AND e.invoice_date >= %s
                    AND e.invoice_date < %s)
                    AND d.user_id = %s
                    GROUP BY d.type_customer
            UNION ALL
                    SELECT SUM(a.price_total),d.type_customer
                    FROM sale_order_line a
                    JOIN product_product b on a.product_id = b.id
                    JOIN product_template c on b.product_tmpl_id = c.id
                    JOIN sale_order d on a.order_id = d.id
                    WHERE (c.categ_id in (1,2) or a.user_id = d.user_id)
                    AND d."state" in ('done','sale')
                    AND d.type_order = 'direct'
                    AND d.name in (SELECT invoice_origin FROM account_move e
                    WHERE "state" = 'posted'
                    AND e.invoice_date >= %s
                    AND e.invoice_date < %s)
                    AND d.user_id = %s
                    GROUP BY d.type_customer
        """
        self._cr.execute(query, (
            date_start, date_end, user_id.id or 0, date_start, date_end, user_id.id or 0, date_start, date_end,
            user_id.id or 0))
        res = self._cr.fetchall()
        amount_khm = 0
        amount_khc = 0
        amount_khtt = 0
        for r in res:
            if r[1] == 'new':
                if r[0]:
                    amount_khm += r[0]
            if r[1] == 'old':
                if r[0]:
                    amount_khc += r[0]
            if r[1] == 'find':
                if r[0]:
                    amount_khtt += r[0]
        amount_total = amount_khm + amount_khc + amount_khtt
        return amount_total, amount_khm, amount_khc, amount_khtt

    # def _sale_order_amount_reality(self, date_start, date_end, user_id):
    #     amount_total = 0
    #     amount_khm = 0
    #     amount_khc = 0
    #     amount_khtt = 0
    #     move_ids = self.env['account.move'].sudo().search(
    #         [('state', '=', 'posted'),
    #          ('invoice_user_id', '=', user_id.id),
    #          ('invoice_date', '>=', date_start),
    #          ('invoice_date', '<=', date_end)])
    #     for move_id in move_ids:
    #         amount_total += move_id.amount_total
    #
    #     move_khm_ids = self.env['account.move'].sudo().search(
    #         [('state', '=', 'posted'),
    #          ('invoice_user_id', '=', user_id.id),
    #          ('sale_id.type_customer', '=', 'new'),
    #          ('invoice_date', '>=', date_start),
    #          ('invoice_date', '<=', date_end)])
    #     for move_id in move_khm_ids:
    #         amount_khm += move_id.amount_total
    #
    #     move_khc_ids = self.env['account.move'].sudo().search(
    #         [('state', '=', 'posted'),
    #          ('invoice_user_id', '=', user_id.id),
    #          ('sale_id.type_customer', '=', 'old'),
    #          ('invoice_date', '>=', date_start),
    #          ('invoice_date', '<=', date_end)])
    #     for move_id in move_khc_ids:
    #         amount_khc += move_id.amount_total
    #
    #     move_khtt_ids = self.env['account.move'].sudo().search(
    #         [('state', '=', 'posted'),
    #          ('invoice_user_id', '=', user_id.id),
    #          ('sale_id.type_customer', '=', 'find'),
    #          ('invoice_date', '>=', date_start),
    #          ('invoice_date', '<=', date_end)])
    #     for move_id in move_khtt_ids:
    #         amount_khtt += move_id.amount_total
    #     return amount_total, amount_khm, amount_khc, amount_khtt

    def onchange_state_end_date_create_line(self, date_start, date_end):
        if date_start and date_end:
            if date_start and date_start + relativedelta(weeks=1) <= date_end:
                qty_lead = self._count_lead(date_start, date_start + relativedelta(weeks=1), self.user_id)
                amount, amount_khm, amount_khc, amount_khtt = self._sale_order_amount_reality(date_start,
                                                                                              date_start + relativedelta(
                                                                                                  weeks=1),
                                                                                              self.user_id)
                vals = {
                    'week': '01',
                    'date_start': date_start,
                    'date_end': date_start + relativedelta(weeks=1),
                    'amount_target': 0,
                    'amount_per_lead_target': 0,
                    'qty_lead_target': 0,
                    'amount_target_khm': 0,
                    'amount_target_khc': 0,
                    'amount_target_khgt': 0,
                    'qty_lead': qty_lead,
                    'amount': amount,
                    'amount_khc': amount_khc,
                    'amount_khtt': amount_khtt,
                    'user_id': self.user_id.id,
                    'team_id': self.team_id.id,
                    'amount_khm': amount_khm,
                    'kpi_id': self.id,
                }
                self.update({'line_ids': [(0, 0, vals)]})
            if date_start and date_start + relativedelta(weeks=2) <= date_end:
                qty_lead = self._count_lead(date_start + relativedelta(weeks=1), date_start + relativedelta(weeks=2),
                                            self.user_id)
                amount, amount_khm, amount_khc, amount_khtt = self._sale_order_amount_reality(
                    date_start + relativedelta(weeks=1),
                    date_start + relativedelta(weeks=2),
                    self.user_id)
                vals = {
                    'week': '02',
                    'date_start': date_start + relativedelta(weeks=1),
                    'date_end': date_start + relativedelta(weeks=2),
                    'amount_target': 0,
                    'amount_per_lead_target': 0,
                    'qty_lead_target': 0,
                    'amount_target_khm': 0,
                    'amount_target_khc': 0,
                    'amount_target_khgt': 0,
                    'user_id': self.user_id.id,
                    'team_id': self.team_id.id,
                    'qty_lead': qty_lead,
                    'amount': amount,
                    'amount_khc': amount_khc,
                    'amount_khm': amount_khm,
                    'amount_khtt': amount_khtt,
                    'kpi_id': self.id,
                }
                self.update({'line_ids': [(0, 0, vals)]})
                if date_start and date_start + relativedelta(weeks=3) <= date_end:
                    qty_lead = self._count_lead(date_start + relativedelta(weeks=2),
                                                date_start + relativedelta(weeks=3),
                                                self.user_id)
                    amount, amount_khm, amount_khc, amount_khtt = self._sale_order_amount_reality(
                        date_start + relativedelta(weeks=2),
                        date_start + relativedelta(weeks=3),
                        self.user_id)
                    vals = {
                        'week': '03',
                        'date_start': date_start + relativedelta(weeks=2),
                        'date_end': date_start + relativedelta(weeks=3),
                        'amount_target': 0,
                        'amount_per_lead_target': 0,
                        'qty_lead_target': 0,
                        'amount_target_khm': 0,
                        'amount_target_khc': 0,
                        'amount_target_khgt': 0,
                        'user_id': self.user_id.id,
                        'team_id': self.team_id.id,
                        'qty_lead': qty_lead,
                        'amount': amount,
                        'amount_khc': amount_khc,
                        'amount_khm': amount_khm,
                        'amount_khtt': amount_khtt,
                        'kpi_id': self.id,
                    }
                    self.update({'line_ids': [(0, 0, vals)]})

                if date_start and date_start + relativedelta(weeks=4) <= date_end:
                    qty_lead = self._count_lead(date_start + relativedelta(weeks=3),
                                                date_start + relativedelta(weeks=4),
                                                self.user_id)
                    amount, amount_khm, amount_khc, amount_khtt = self._sale_order_amount_reality(
                        date_start + relativedelta(weeks=3),
                        date_start + relativedelta(weeks=4),
                        self.user_id)
                    vals = {
                        'week': '04',
                        'date_start': date_start + relativedelta(weeks=3),
                        'date_end': date_start + relativedelta(weeks=4),
                        'amount_target': 0,
                        'amount_per_lead_target': 0,
                        'qty_lead_target': 0,
                        'amount_target_khm': 0,
                        'amount_target_khc': 0,
                        'amount_target_khgt': 0,
                        'user_id': self.user_id.id,
                        'team_id': self.team_id.id,
                        'qty_lead': qty_lead,
                        'amount': amount,
                        'amount_khc': amount_khc,
                        'amount_khm': amount_khm,
                        'amount_khtt': amount_khtt,
                        'kpi_id': self.id,
                    }
                    self.update({'line_ids': [(0, 0, vals)]})
                if date_start and date_start + relativedelta(weeks=5) <= date_end:
                    qty_lead = self._count_lead(date_start + relativedelta(weeks=4),
                                                date_start + relativedelta(weeks=5),
                                                self.user_id)
                    amount, amount_khm, amount_khc, amount_khtt = self._sale_order_amount_reality(
                        date_start + relativedelta(weeks=4),
                        date_start + relativedelta(weeks=5),
                        self.user_id)
                    vals = {
                        'week': '05',
                        'date_start': date_start + relativedelta(weeks=4),
                        'date_end': date_end,
                        'amount_target': 0,
                        'amount_per_lead_target': 0,
                        'qty_lead_target': 0,
                        'amount_target_khm': 0,
                        'amount_target_khc': 0,
                        'amount_target_khgt': 0,
                        'user_id': self.user_id.id,
                        'team_id': self.team_id.id,
                        'qty_lead': qty_lead,
                        'amount': amount,
                        'amount_khc': amount_khc,
                        'amount_khm': amount_khm,
                        'amount_khtt': amount_khtt,
                        'kpi_id': self.id,
                    }
                    self.update({'line_ids': [(0, 0, vals)]})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('crm.kpi.sale') or '/'
        kpi = super(CRMKpisale, self).create(vals)
        return kpi

    def action_confirm(self):
        self.state = 'confirmed'

    def action_cancel(self):
        self.state = 'cancel'


class CRMKpisaleLine(models.Model):
    _name = 'crm.kpi.sale.line'

    kpi_id = fields.Many2one('crm.kpi.sale', string='KPI')
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
    team_id = fields.Many2one('crm.team', string='Nhóm')
    amount_target = fields.Integer(string='Doanh thu KH', required=True)
    amount = fields.Integer(string='Doanh thu TT')
    amount_per_lead_target = fields.Integer(string='Doanh thu/ Lead KH', required=True)
    amount_per_lead = fields.Integer(string='Doanh thu/ Lead TT')
    qty_lead_target = fields.Integer(string='Số Lead KH', required=True)
    qty_lead = fields.Integer(string='Số Lead TT')
    amount_target_khm = fields.Integer(string='Doanh thu KH KHM', required=True)
    amount_khm = fields.Integer(string='Doanh thu TT KHM')
    amount_target_khc = fields.Integer(string='Doanh thu KH KHC', required=True)
    amount_khc = fields.Integer(string='Doanh thu TT KHC')
    amount_target_khgt = fields.Integer(string='Doanh thu KH KHGT', required=True)
    amount_khgt = fields.Integer(string='Doanh thu TT KHGT')
    amount_khtt = fields.Integer(string='Doanh thu TT KHTT')

    def _get_nextcall_weekly_leave(self, month, day):
        date_1 = date.today()
        start_date = datetime(date_1.year, month, day)
        end_date = datetime(date_1.year, month, calendar.mdays[month])
        return start_date, end_date

    @api.onchange('week')
    def onchange_state_end_date(self):
        if self.kpi_id.date_start and self.week:
            self.date_start = self.kpi_id.date_start + relativedelta(weeks=(int(self.week) - 1))
            self.date_end = self.date_start + relativedelta(weeks=1)

    @api.onchange('amount', 'qty_lead')
    def onchange_amount_per_lead(self):
        if self.amount > 0 and self.qty_lead > 0:
            self.amount_per_lead = self.amount / self.qty_lead

    @api.onchange('date_start', 'date_end', 'user_id')
    def _onchange_amount_total(self):
        for s in self:
            if s.date_start and s.date_end:
                amount, amount_khm, amount_khc, amount_khtt = s.kpi_id._sale_order_amount_reality(s.date_start,
                                                                                                  s.date_end,
                                                                                                  self.user_id)
                # sale_ids = self.env['sale.order'].sudo().search(
                #     [('user_id', '=', s.user_id.id), ('date_order', '>=', s.date_start),
                #      ('date_order', '<=', s.date_end), ('state', 'in', ('draft', 'sale', 'done'))])
                # amount_total = 0
                # for sale_id in sale_ids:
                #     amount_total += sale_id.amount_total
                s.amount = amount

    @api.onchange('date_start', 'date_end', 'user_id')
    def _onchange_lead_count(self):
        for s in self:
            if s.date_start and s.date_end:
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', s.user_id.id), ('date_open', '>=', s.date_start),
                     ('date_open', '<=', s.date_end), ('stage_id', 'not in', (2, 15, 16))])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                s.qty_lead = lead_count


class CRMKpisaleLineDay(models.Model):
    _name = 'crm.kpi.sale.line.day'

    kpi_id = fields.Many2one('crm.kpi.sale', string='KPI')
    date = fields.Date(string="Ngày", required=True)
    user_id = fields.Many2one('res.users', string='Nhân viên')
    amount = fields.Integer(string='Doanh thu dự kiến')
    amount_reality = fields.Integer(string='Doanh thu thực tế')
    qty_lead = fields.Integer(string='Số Lead hợp lệ')
    qty_lead_kh = fields.Integer(string='Số Lead / Ngày', store=True, compute="_qty_lead_kh")
    amount_khm = fields.Integer(string='Doanh thu KHM')
    amount_khc = fields.Integer(string='Doanh thu KHC')
    amount_khgt = fields.Integer(string='Doanh thu TT KHGT')
    amount_khtt = fields.Integer(string='Doanh thu TT KHTT')

    @api.depends('kpi_id.lead_count_kpi_per_day')
    def _qty_lead_kh(self):
        """
        Compute the total amounts of the SO.
        """
        for day in self:
            day.update({
                'qty_lead_kh': day.kpi_id.lead_count_kpi_per_day,
            })

    @api.onchange('date', 'user_id')
    def _onchange_amount_total(self):
        for s in self:
            if s.date:
                sale_ids = self.env['sale.order'].sudo().search(
                    [('user_id', '=', s.user_id.id), ('date_order', '>=', s.date),
                     ('date_order', '<=', s.date), ('state', 'in', ('draft', 'sale', 'done'))])
                amount_total = 0
                for sale_id in sale_ids:
                    amount_total += sale_id.amount_total
                s.amount = amount_total

                sale_khc_ids = self.env['sale.order'].sudo().search(
                    [('user_id', '=', s.user_id.id), ('date_order', '>=', s.date),
                     ('date_order', '<=', s.date), ('type_customer', '=', 'old'),
                     ('state', 'in', ('draft', 'sale', 'done'))])
                amount_khc = 0
                for sale_id in sale_khc_ids:
                    amount_khc += sale_id.amount_total
                s.amount_khc = amount_khc

                sale_khm_ids = self.env['sale.order'].sudo().search(
                    [('user_id', '=', s.user_id.id), ('date_order', '>=', s.date),
                     ('date_order', '<=', s.date), ('type_customer', '=', 'new'),
                     ('state', 'in', ('draft', 'sale', 'done'))])
                amount_khm = 0
                for sale_id in sale_khm_ids:
                    amount_khm += sale_id.amount_total
                s.amount_khm = amount_khm

    @api.onchange('date', 'user_id')
    def _onchange_lead_count(self):
        for s in self:
            if s.date:
                lead_ids = self.env['crm.lead'].sudo().search(
                    [('user_id', '=', s.user_id.id), ('date_open', '>=', s.date),
                     ('date_open', '<=', s.date), ('stage_id', 'not in', (2, 15, 16))])
                lead_count = 0
                for lead_id in lead_ids:
                    lead_count += 1
                s.qty_lead = lead_count


class CRMKpisaleLineSaleOrder(models.Model):
    _name = 'crm.kpi.sale.line.sale.order'

    kpi_id = fields.Many2one('crm.kpi.sale', string='KPI')
    date = fields.Date(string="Ngày đơn hàng", required=True)
    date_fill = fields.Date(string="Ngày lọc")
    date_invoice = fields.Date(string="Ngày Hóa đơn")
    user_id = fields.Many2one('res.users', string='Nhân viên')
    team_id = fields.Many2one('crm.team', string='Nhóm')
    amount = fields.Integer(string='Doanh thu dự kiến')
    amount_reality = fields.Integer(string='Doanh thu thực tế')
    order_id = fields.Many2one('sale.order', string="Đơn hàng")
    type_customer_order = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', related='order_id.type_customer')


class CRMKpisaleLineSaleOrder2(models.Model):
    _name = 'crm.kpi.sale.line.sale.order2'

    kpi_id = fields.Many2one('crm.kpi.sale', string='KPI')
    date = fields.Date(string="Ngày đơn hàng", required=True)
    date_fill = fields.Date(string="Ngày lọc")
    date_invoice = fields.Date(string="Ngày hóa đơn")
    user_id = fields.Many2one('res.users', string='Nhân viên')
    team_id = fields.Many2one('crm.team', string='Nhóm')
    amount = fields.Integer(string='Doanh thu dự kiến')
    amount_reality = fields.Integer(string='Doanh thu thực tế')
    order_id = fields.Many2one('sale.order', string="Đơn hàng")
    type_customer_order = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', related='order_id.type_customer')
