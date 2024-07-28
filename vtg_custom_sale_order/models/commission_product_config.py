# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class CommissionProductConfig(models.Model):
    _name = 'commission.product.config'

    type = fields.Selection([
        ('employee', 'Nhân viên sale'),
        ('master', 'Thợ chính'),
        ('assistant', 'Thợ phụ'),
    ], 'Loại', required=1)
    discount_type = fields.Selection([
        ('fixed', 'Tiền cố định'),
        ('percent', 'Phần trăm'),
    ], 'Loại chiết khấu', required=1)
    discount = fields.Integer('Chiết khấu')
    rate = fields.Float('Hệ số', default=1)
    product_id = fields.Many2one('product.product', 'Sản phẩm', required=1)
