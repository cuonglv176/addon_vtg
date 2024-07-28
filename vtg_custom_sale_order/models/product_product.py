# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    commission_config_ids = fields.One2many('commission.product.config', 'product_id', 'Cấu hình hoa hồng')
