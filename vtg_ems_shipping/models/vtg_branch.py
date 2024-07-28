# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class VTGBranch(models.Model):
    _inherit = 'vtg.branch'

    ems_token = fields.Char('Token')
