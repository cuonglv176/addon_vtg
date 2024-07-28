# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class VTGStockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    product_qty_available = fields.Float('Số lượng tồn', related='product_id.qty_available', depends=['product_id'])

    @api.model
    def default_get(self, fields):
        vals = super(VTGStockMoveLine, self).default_get(fields)

        return vals
