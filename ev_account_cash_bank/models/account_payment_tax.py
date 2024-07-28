# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class AccountPaymentTax(models.Model):
    _name = 'account.payment.tax'

    payment_id = fields.Many2one('account.payment.cash.bank', 'Account Payment', ondelete='cascade')
    name = fields.Char('Description')
    account_tax_id = fields.Many2one('account.account', 'Account Tax')
    amount_tax = fields.Monetary('Amount tax')
    percent_tax = fields.Float('Percent Tax')
    amount_invoice = fields.Monetary('Amount invoice before tax')
    date_invoice = fields.Date('Date Invoice')
    code_invoice = fields.Char('Code Invoice')
    number_invoice = fields.Char('Number Invoice')
    partner_id = fields.Many2one('res.partner', 'Vendor')
    currency_id = fields.Many2one('res.currency', string='Currency')
    number_invoice_form = fields.Char('Number Invoice Form')

    @api.onchange('amount_invoice', 'percent_tax')
    def onchange_amount_tax(self):
        if self.amount_invoice and self.percent_tax:
            self.amount_tax = (self.amount_invoice / 100) * self.percent_tax
        else:
            self.amount_tax = 0