# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)


class AccountPaymentLine(models.Model):
    _name = 'account.payment.line'
    _description = 'Account Payment Cash Line'

    def _domain_account(self):
        ids = []
        account = self.env['account.account'].search([('company_id', '=', self.env.company.id)], order='code')
        for a in account:
            ids.append(a.id)
        return [('id', 'in', ids)]

    payment_id = fields.Many2one('account.payment.cash.bank', string='Payment', ondelete='cascade')
    name = fields.Char('Description')
    value = fields.Float('Value')
    value_natural_currency = fields.Float('Value currency')
    debit_account_id = fields.Many2one('account.account', 'Accounting Debit account', domain=_domain_account)
    credit_account_id = fields.Many2one('account.account', 'Accounting Credit account', domain=_domain_account)
    partner_id = fields.Many2one('res.partner', 'Partner')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    account_expense_item_id = fields.Many2one('account.expense.item', 'Account Expense Item')
    check_required_analytic = fields.Boolean(default=False)
    check_required_expense_item = fields.Boolean(default=False)

    @api.onchange('debit_account_id', 'credit_account_id')
    def onechange_check_required(self):
        if self.debit_account_id.x_required_analytic or self.credit_account_id.x_required_analytic:
            self.check_required_analytic = True
        if self.debit_account_id.x_required_expense_item or self.credit_account_id.x_required_expense_item:
            self.check_required_expense_item = True


    @api.onchange('value')
    def onchange_value(self):
        if self.value:
            if self.payment_id.rate and self.payment_id.rate != 0:
                self.value_natural_currency = self.value * self.payment_id.rate
            else:
                self.value_natural_currency = self.value
