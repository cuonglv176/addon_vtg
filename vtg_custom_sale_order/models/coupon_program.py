# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class CouponProgram(models.Model):
    _inherit = "coupon.program"

    product_category_ids = fields.Many2many('product.category', string='Nhóm sản phẩm')

    @api.onchange('product_category_ids')
    def onchange_product_category_ids(self):
        if self.product_category_ids:
            product = []
            for category_id in self.product_category_ids:
                product_ids = self.env['product.product'].search([('categ_id', '=', category_id._origin.id)])
                for p in product_ids:
                    product.append(p.id)
            self.discount_specific_product_ids = [(6, 0, product)]
            # self.discount_specific_product_ids = [(4, product_ids)]
