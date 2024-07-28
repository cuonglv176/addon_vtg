# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CrmMKTpayment(models.Model):
    _name = 'crm.mkt.payment'
    _description = 'MKT payment'
    _order = 'create_date desc'

    date = fields.Date(string="Ngày", required=True, default=fields.Date.today())
    user_id = fields.Many2one('res.users', string='Nhân viên', required=True, default=lambda self: self.env.user)
    reason = fields.Text('Lý do')
    amount = fields.Integer(string='Số tiền')
    bank = fields.Char(string='Thông tin TK nhận')
    lead_check = fields.Boolean(string='Lead Check')
    amount_account = fields.Integer(string='Kế toán chi')
    receive = fields.Boolean(string='Đã nhận')
    currency_id = fields.Many2one('res.currency', string='tiền tệ', default=23)
