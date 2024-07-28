# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    x_allow_record_account_move = fields.Integer('Allow access to the following journal entries')
