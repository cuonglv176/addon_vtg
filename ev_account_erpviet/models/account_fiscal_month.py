# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountFiscalMonth(models.Model):
    _name = 'account.fiscal.month'

    name = fields.Char('Name')
    date_from = fields.Date(string='Start Date', required=True,
                            help='Start Date, included in the fiscal year.')
    date_to = fields.Date(string='End Date', required=True,
                          help='Ending Date, included in the fiscal year.')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    account_fiscal_year_id = fields.Many2one('account.fiscal.year', 'Account Fiscal Year')


class AccountFiscalYear(models.Model):
    _inherit = 'account.fiscal.year'

    lines = fields.One2many('account.fiscal.month', 'account_fiscal_year_id', 'Account Fiscal Month')