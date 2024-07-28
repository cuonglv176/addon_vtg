# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_director = fields.Char('Director')
    x_chief_accountant = fields.Char('Chief Accountant')
