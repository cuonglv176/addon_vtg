# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _, tools

_logger = logging.getLogger(__name__)


class VTGRportSaleCustomerBuyMonth(models.Model):
    _name = 'vtg.report.sale.buy.month'
    _description = 'VTG Report Customer buy month'
    _auto = False

    count_buy = fields.Integer(string='Số đơn mua')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    phone = fields.Char(string='Số Điện Thoại')
    branch_id = fields.Many2one('vtg.branch', string='Chi nhánh')
    date = fields.Date(string='Tháng')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
             SELECT ROW_NUMBER() OVER (ORDER BY a.date,a.partner_id, a.branch_id) AS id, 
             COUNT(*) as count_buy, a.partner_id,b.phone,a.branch_id,a.date FROM (
             SELECT partner_id,x_branch_id as branch_id,DATE_TRUNC('month', date_order) AS date
             FROM sale_order WHERE create_date >= '01/01/2024' AND state in ('paid','done','invoiced')) as a
             Join res_partner as b on a.partner_id = b.id
             GROUP BY a.partner_id,a.branch_id,a.date, b.phone
            )''' % (self._table,)
                            )


class VTGRportSale(models.Model):
    _name = 'vtg.report.sale.pos'
    _description = 'VTG Report sale pos'
    _auto = False

    amount_for_sale = fields.Monetary(string="Doanh số được tính")
    amount_total = fields.Monetary(string="Tổng")
    user_id = fields.Many2one('res.users', string="Nhân viên kinh doanh")
    team_id = fields.Many2one('crm.team', string="Nhóm bán hàng")
    marketing_id = fields.Many2one('res.users', string="Marketing")
    department_id = fields.Many2one('hr.department', string="Phòng ban")
    date = fields.Date(string="Ngày")
    sale_id = fields.Many2one('sale.order', string='Đơn hàng Sale')
    order_id = fields.Many2one('pos.order', string='Đơn hàng POS')
    currency_id = fields.Many2one('res.currency', string='Tiền')
    type_customer = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', default='new')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    source_id = fields.Many2one('utm.source', string='Nguồn')
    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT ROW_NUMBER() OVER (ORDER BY a.date,a.user_id, a.marketing_id) AS id,a.amount_for_sale ,a.amount_total,a.user_id, a.team_id,a.marketing_id,a.department_id,
            a.date, a.sale_id,a.order_id,23 currency_id,type_customer,partner_id,source_id,channel_id
            FROM (
            SELECT a.amount_for_sale ,a.amount_total,a.user_id, a.team_id,a.marketing_id,a.department_id,
            a.date_order :: DATE as date, a.id sale_id,NULL order_id, a.currency_id,type_customer,partner_id,source_id,channel_id
            FROM sale_order a 
            WHERE date_order >= '01/09/2023' AND state in ('sale','done')
            UNION ALL
            SELECT a.amount_for_sale ,a.amount_total,a.user_id, a.crm_team_id as team_id,a.marketing_id,a.department_id,
             a.date_order :: DATE as date, NULL sale_id,a.id order_id, 23 currency_id,type_customer,partner_id,source_id,channel_id
            FROM pos_order a 
            WHERE date_order >= '01/09/2023' AND state in ('paid','done','invoiced')
            ) as a
            )''' % (self._table,)
                            )
