# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    x_corporate_funds = fields.Boolean(string='Corporate Funds', default=False)
