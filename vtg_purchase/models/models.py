# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class VTGPurchaseRequest(models.Model):
    _name = 'vtg.purchase.request'

    date_request = fields.Date(string='Ngày gửi yêu cầu', default=fields.Date.today)
    user_id = fields.Many2one('res.users', string='Người yêu cầu', default=lambda self: self.env.uid)
    product_tmpl_ids = fields.Many2many('product.template', string='Mã sản phẩm')
    qty = fields.Integer(string='Số lượng')
    date = fields.Date(string='Ngày cần')
    request_note = fields.Text(string='Yêu cầu khác')
    img = fields.Binary(string='Ảnh hóa đơn cọc (nếu có)')
    note = fields.Text(string='Ghi chú thu mua')

    order = fields.Char(string='Báo giá')
    approve = fields.Selection([
        ('buy', 'Mua'),
        ('not_buy', 'Không mua')], string='Thu mua xác nhận')
