# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _, tools

_logger = logging.getLogger(__name__)


class VTGRportCRM(models.Model):
    _name = 'vtg.report.crm'
    _description = 'VTG Report CRM'
    _auto = False

    amount_total = fields.Integer(string="Doanh số")
    amount = fields.Integer(string="Doanh thu")
    user_id = fields.Many2one('res.users', string="Sale")
    marketing_id = fields.Many2one('res.users', string="Marketing")
    date = fields.Date(string="Ngày")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT ROW_NUMBER() OVER (ORDER BY a.date,a.user_id, a.marketing_id) AS id, SUM(amount_total) amount_total,
            SUM(amount) amount, a.user_id, a.marketing_id, a.date
            FROM (
            SELECT a.amount_total amount_total, 0 amount,a.user_id, 
            a.marketing_id, a.date_order :: DATE as date
            FROM sale_order a 
            WHERE create_date > '01/01/2023' AND state in ('sale','done')
            UNION
            SELECT a.amount_total amount_total, 0 amount,a.user_id, 
            a.marketing_id, a.date_order :: DATE as date
            FROM pos_order a 
            WHERE create_date > '01/01/2023' AND state in  ('paid','done','invoiced')
            UNION
            SELECT 0 amount_total, a.amount_total amount,
            a.invoice_user_id user_id,a.marketing_id,a.invoice_date:: DATE as date
            FROM account_move a 
            WHERE create_date > '01/01/2023' 
            and state = 'posted' and (sale_id is not NULL or pos_order_id is not NULL) 
            ) as a
            WHERE a.date is NOT NULL
            GROUP BY a.user_id, a.marketing_id, a.date
            )''' % (self._table,)
                            )


class VTGRportCRMSALEAMOUNT(models.Model):
    _name = 'vtg.report.crm.sale.amount'
    _description = 'VTG Report Sale Amount'
    _auto = False

    amount_total = fields.Integer(string="Doanh số")
    amount = fields.Integer(string="Doanh thu")
    user_id = fields.Many2one('res.users', string="Sale")
    date = fields.Date(string="Ngày")

    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     self.env.cr.execute('''
    #         CREATE OR REPLACE VIEW %s AS (
    #         SELECT ROW_NUMBER() OVER (ORDER BY a.date) AS id, amount_total,amount, a.user_id,a.date
    #         FROM (
    #         SELECT 0 amount_total,SUM(amount) amount, a.user_id,a.date
    #         FROM (
    #         SELECT amount_total amount, a.invoice_user_id user_id,a.invoice_date:: DATE as date
    #         FROM account_move a
    #         WHERE create_date > '01/01/2023'
    #         and state = 'posted' and (sale_id is not NULL or pos_order_id is not NULL) ) as a
    #         GROUP BY a.user_id,a.date
    #         UNION ALL
    #         SELECT SUM(amount_total) amount_total,0 amount, a.user_id,a.date
    #         FROM (
    #         SELECT a.amount_total amount_total, a.user_id, a.date_order :: DATE as date
    #         FROM sale_order a
    #         WHERE create_date > '01/01/2023'
    #         AND state in ('sale','done')
    #         UNION ALL
    #         SELECT a.amount_total amount_total, a.user_id, a.date_order :: DATE as date
    #         FROM pos_order a
    #         WHERE create_date > '01/01/2023'
    #         AND state in ('paid','done','invoiced')
    #         ) as a
    #         GROUP BY a.user_id,a.date) as a
    #
    #         )''' % (self._table,)
    #                         )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT ROW_NUMBER() OVER (ORDER BY a.date) AS id, amount_total,amount, a.user_id,a.date
            FROM (
            SELECT 0 amount_total,SUM(amount) amount, a.user_id,a.date
            FROM (
            SELECT amount_total amount, a.invoice_user_id user_id,a.invoice_date:: DATE as date
            FROM account_move a 
            WHERE create_date > '01/01/2023' 
            and state = 'posted' and (sale_id is not NULL or pos_order_id is not NULL) ) as a 
            GROUP BY a.user_id,a.date
            UNION ALL
            SELECT SUM(amount_total) amount_total,0 amount, a.user_id,a.date
            FROM (
            SELECT a.amount_total amount_total, a.user_id, a.date_order :: DATE as date
            FROM sale_order a 
            WHERE create_date > '01/01/2023' 
            AND state not in ('draft','cancel') and status_transfer != 'return'
            ) as a
            GROUP BY a.user_id,a.date) as a

            )''' % (self._table,)
                            )


class VTGRportCRMMKTAMOUNT(models.Model):
    _name = 'vtg.report.crm.mkt.amount'
    _description = 'VTG Report mkt Amount'
    _auto = False

    amount_total = fields.Integer(string="Doanh số")
    amount = fields.Integer(string="Doanh thu")
    marketing_id = fields.Many2one('res.users', string="MKT")
    date = fields.Date(string="Ngày")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            SELECT ROW_NUMBER() OVER (ORDER BY a.date) AS id, amount_total,amount, a.marketing_id,a.date
            FROM (
            SELECT 0 amount_total,SUM(amount) amount, a.marketing_id,a.date
            FROM (
            SELECT amount_total amount, a.marketing_id marketing_id,a.invoice_date:: DATE as date
            FROM account_move a
            WHERE create_date > '01/01/2023'
            and state = 'posted' and (sale_id is not NULL or pos_order_id is not NULL)) as a
            GROUP BY a.marketing_id,a.date
            UNION ALL
            SELECT SUM(amount_total) amount_total,0 amount, a.marketing_id,a.date
            FROM (
            SELECT a.amount_total amount_total, a.marketing_id, a.date_order :: DATE as date
            FROM sale_order a
            WHERE create_date > '01/01/2023'
            AND state in ('sale','done') ) as a
            GROUP BY a.marketing_id,a.date
            UNION ALL
            SELECT SUM(amount_total) amount_total,0 amount, a.marketing_id,a.date
            FROM (
            SELECT a.amount_total amount_total, a.marketing_id, a.date_order :: DATE as date
            FROM pos_order a
            WHERE create_date > '01/01/2023'
            AND state in ('paid','done','invoiced')) as a
            GROUP BY a.marketing_id,a.date
            ) as a
            )''' % (self._table,)
                            )
    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     self.env.cr.execute('''
    #         CREATE OR REPLACE VIEW %s AS (
    #         SELECT ROW_NUMBER() OVER (ORDER BY a.date) AS id, amount_total,amount, a.marketing_id,a.date
    #         FROM (
    #         SELECT 0 amount_total,SUM(amount) amount, a.marketing_id,a.date
    #         FROM (
    #         SELECT amount_for_sale1 amount, a.marketing_id marketing_id,a.date_order:: DATE as date
    #         FROM account_move a
    #         WHERE create_date > '01/01/2023'
    #         and state = 'posted' and (sale_id is not NULL or pos_order_id is not NULL) AND a.type_customer = 'new') as a
    #         GROUP BY a.marketing_id,a.date
    #         UNION ALL
    #         SELECT 0 amount_total,SUM(amount) amount, a.marketing_id,a.date
    #         FROM (
    #         SELECT amount_for_sale1 amount, a.marketing_id marketing_id,a.create_lead:: DATE as date
    #         FROM account_move a
    #         WHERE create_date > '01/01/2023'
    #         and state = 'posted' and (sale_id is not NULL or pos_order_id is not NULL) AND a.type_customer = 'old') as a
    #         GROUP BY a.marketing_id,a.date
    #         UNION ALL
    #         SELECT SUM(amount_total) amount_total,0 amount, a.marketing_id,a.date
    #         FROM (
    #         SELECT a.amount_for_sale amount_total, a.marketing_id, a.create_date :: DATE as date
    #         FROM sale_order a
    #         WHERE create_date > '01/01/2023'
    #         AND state in ('sale','done') AND a.type_customer = 'new') as a
    #         GROUP BY a.marketing_id,a.date
    #         UNION ALL
    #         SELECT SUM(amount_total) amount_total,0 amount, a.marketing_id,a.date
    #         FROM (
    #         SELECT a.amount_for_sale amount_total, a.marketing_id, a.create_lead :: DATE as date
    #         FROM sale_order a
    #         WHERE create_date > '01/01/2023'
    #         AND state in ('sale','done') AND a.type_customer = 'old') as a
    #         GROUP BY a.marketing_id,a.date
    #         ) as a
    #         )''' % (self._table,)
    #                         )


class VTGRportCRMLEADSALE(models.Model):
    _name = 'vtg.report.crm.lead.sale'
    _description = 'VTG Report lead sale'
    _auto = False

    count_lead = fields.Integer(string="Số lead")
    user_id = fields.Many2one('res.users', string="Sale")
    date = fields.Date(string="Ngày")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            			SELECT ROW_NUMBER() OVER (ORDER BY date_open::DATE,user_id) AS id,
                        COUNT(*) count_lead,user_id,date_open::DATE as date
                        FROM crm_lead 
                        WHERE create_date > '01/01/2023'
                        GROUP BY user_id,date_open::DATE
            )''' % (self._table,)
                            )


class VTGRportCRMLOGSALE(models.Model):
    _name = 'vtg.report.crm.log.sale'
    _description = 'VTG Report log sale'
    _auto = False

    count_log = fields.Integer(string="Số ghi chú")
    user_id = fields.Many2one('res.users', string="Sale")
    date = fields.Date(string="Ngày")
    contact_form = fields.Selection(
        [('video', 'Video Call'),
         ('tele_sale', 'Tele sale'),
         ('chat', 'Chat'),
         ('meeting', 'Gặp mặt'),
         ('survey', 'Gửi khảo sát'),
         ('other', 'Khác')],
        string="Hình thức liên hệ",
        default='tele_sale')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
            	SELECT ROW_NUMBER() OVER (ORDER BY create_date::DATE,create_uid) AS id,
                COUNT(*) count_log,create_uid as user_id,create_date::DATE as date, contact_form
                FROM crm_lead_log_note
                WHERE create_date > '01/01/2023'
                GROUP BY user_id,create_date::DATE,contact_form
            )''' % (self._table,)
                            )


class VTGRportCRMBOONGSALE(models.Model):
    _name = 'vtg.report.crm.booking.sale'
    _description = 'VTG Report booking sale'
    _auto = False

    count_booking = fields.Integer(string="Số booing")
    user_id = fields.Many2one('res.users', string="Sale")
    date = fields.Date(string="Ngày")
    branch_id = fields.Many2one('vtg.branch', string="Chi nhánh")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
              CREATE OR REPLACE VIEW %s AS (
              	SELECT ROW_NUMBER() OVER (ORDER BY date_sent::DATE,user_id,branch_id) AS id,
                COUNT(*) count_booking,user_id as user_id,date_sent::DATE as date, branch_id
                FROM crm_lead_booking
                WHERE create_date > '01/01/2023'
                GROUP BY user_id,date_sent::DATE,branch_id
              )''' % (self._table,)
                            )


class VTGRportCRMCOUNTSALE(models.Model):
    _name = 'vtg.report.crm.count.sale'
    _description = 'VTG Report order sale'
    _auto = False

    count_order = fields.Integer(string="Số đơn")
    user_id = fields.Many2one('res.users', string="Sale")
    date = fields.Date(string="Ngày")
    type_customer = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', default='new')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
              CREATE OR REPLACE VIEW %s AS (
              		SELECT ROW_NUMBER() OVER (ORDER BY date_order::DATE,user_id) AS id,
                    COUNT(*) count_order,user_id,date_order::DATE as date, type_customer
                    FROM sale_order 
                    WHERE create_date > '01/01/2023' and state in ('sale','done')
                    GROUP BY user_id,date_order::DATE,type_customer
              )''' % (self._table,)
                            )


class VTGRportListSale(models.Model):
    _name = 'vtg.report.crm.list.sale'
    _description = 'VTG Report list sale'
    _auto = False

    user_id = fields.Many2one('res.users', string="Sale")
    date = fields.Date(string="Ngày")
    count_lead = fields.Integer(string="Số lead")
    count_order = fields.Integer(string="Số đơn")
    count_booking = fields.Integer(string="Số booking")
    amount_total = fields.Float(string="Doanh số")
    amount_for_sale = fields.Float(string="Doanh thu")
    rate = fields.Float(string="Tỉ lệ chốt")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
              CREATE OR REPLACE VIEW %s AS (
              	SELECT ROW_NUMBER() OVER (ORDER BY a.user_id,a.date) AS id,
                a.user_id,a.date, SUM(count_lead) count_lead, SUM(count_booking) count_booking, 
                SUM(count_order) count_order, SUM(amount_total) amount_total,
                SUM(amount_for_sale) amount_for_sale, 0  rate
                FROM (
                SELECT a.user_id,a.date, 0 count_lead,0 count_booking, 
                0 count_order,0 amount_total,SUM(amount) amount_for_sale
                FROM (
                SELECT amount_total amount, a.invoice_user_id user_id,a.invoice_date:: DATE as date
                FROM account_move a 
                WHERE create_date > '01/01/2023' 
                and state = 'posted' and (sale_id is not NULL or pos_order_id is not NULL)) as a
                GROUP BY user_id,date
                UNION ALL
                SELECT a.user_id,a.date, 0 count_lead,0 count_booking, 
                0 count_order,SUM(amount_total) amount_total,0 amount_for_sale
                FROM (
                SELECT a.amount_total amount_total, a.user_id, a.date_order :: DATE as date
                FROM sale_order a 
                WHERE create_date > '01/01/2023' 
                AND state in ('sale','done')) as a
                GROUP BY a.user_id,a.date
                UNION ALL
                SELECT user_id,date_open::DATE as date,COUNT(*) count_lead,
                0 count_booking, 0 count_order,0 amount_total,0 amount_for_sale
                FROM crm_lead 
                WHERE create_date > '01/01/2023'
                GROUP BY user_id,date_open::DATE 
                UNION ALL
                SELECT  user_id,date_sent::DATE as date,0 count_lead,
                COUNT(*) count_booking , 0 count_order,0 amount_total,0 amount_for_sale
                FROM crm_lead_booking
                WHERE create_date > '01/01/2023'
                GROUP BY user_id,date_sent::DATE
                UNION ALL
                SELECT user_id,date_order::DATE as date,0 count_lead,
                0 count_booking , COUNT(*) count_order,0 amount_total,0 amount_for_sale
                FROM sale_order 
                WHERE create_date > '01/01/2023' and state in ('sale','done')
                GROUP BY user_id,date_order::DATE) as a
                GROUP BY a.user_id,a.date
              )''' % (self._table,)
                            )


class VTGRportPriceLeadMKT(models.Model):
    _name = 'vtg.report.crm.price.lead.mkt'
    _description = 'VTG Report price lead mkt'
    _auto = False

    price_lead = fields.Integer(string="Giá lead")
    marketing_id = fields.Many2one('res.users', string="Nhân viên")
    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh')
    date = fields.Date(string="Ngày")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
              CREATE OR REPLACE VIEW %s AS (
              	SELECT ROW_NUMBER() OVER (ORDER BY date_trunc('month', current_date)) AS id,(budget/sl) As price_lead,a.marketing_id, a.channel_id,date_trunc('month', current_date) date
                FROM (
                SELECT COUNT(*) sl, marketing_id, channel_id
                FROM crm_lead 
                WHERE create_date > date_trunc('month', current_date) - interval '1 day' and old_lead_id is null
                GROUP BY marketing_id,channel_id) as a
                JOIN (
                SELECT SUM(budget) budget, user_id, channel_id
                FROM crm_kpi_mkt_budget 
                WHERE date > date_trunc('month', current_date) - interval '1 day' 
                GROUP BY user_id,channel_id) as b 
                ON a.marketing_id = b.user_id AND a.channel_id = b.channel_id
              )''' % (self._table,)
                            )
