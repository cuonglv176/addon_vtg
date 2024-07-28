# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class OrderLineUser(models.Model):
    _name = 'order.line.user'

    type = fields.Selection([
        ('employee', 'Nhân viên sale'),
        ('master', 'Thợ chính'),
        ('assistant', 'Thợ phụ'),
    ], 'Loại', required=1)
    user_id = fields.Many2one('res.users', 'Nhân viên')
    discount_type = fields.Selection([
        ('fixed', 'Tiền cố định'),
        ('percent', 'Phần trăm'),
    ], 'Loại chiết khấu', required=1)
    discount = fields.Integer('Chiết khấu')
    rate = fields.Float('Hệ số', default=1)
    amount = fields.Float('Tiền được nhận')
    sale_line_id = fields.Many2one('sale.order.line', 'Chi tiết bán hàng')
    pos_line_id = fields.Many2one('pos.order.line', 'Chi tiết bán hàng POS')

    @api.onchange('discount_type', 'discount', 'sale_line_id', 'pos_line_id')
    def _onchange_compute_amount(self):
        if self.discount_type == 'fixed':
            self.amount = self.discount * self.rate
        elif self.discount_type == 'percent':
            if self.sale_line_id:
                sale_price = self.sale_line_id.price_total
            elif self.pos_line_id:
                sale_price = self.pos_line_id.price_total
            else:
                sale_price = 0
            self.amount = sale_price * self.discount / 100
