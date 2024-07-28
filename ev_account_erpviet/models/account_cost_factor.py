# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import osv


class CostFactor(models.Model):
    _name = 'cost.factor'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    code = fields.Char(string='Code')
    is_raw_material_directly = fields.Boolean('Raw Material Directly')