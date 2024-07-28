# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CRMLEADPayment(models.Model):
    _name = 'vtg.crm.mkt.payment'

    date = fields.Date(string="Ngày", required=True)
    user_id = fields.Many2one('res.users', string='Nhân viên')
    reason = fields.Text('Lý do')
    amount = fields.Float(string='Số tiền')
    bank = fields.Char(string='Thông tin TK nhận')
    lead_check = fields.Boolean(string='Lead Check')
    amount_account = fields.Float(string='Kế toán chi')
    receive = fields.Boolean(string='Đã nhận')
    currency_id = fields.Many2one('res.currency', string='tiền tệ', default=23)
