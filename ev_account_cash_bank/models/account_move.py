# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_payment_option_id = fields.Many2one('account.payment.cash.bank', 'Accountant Payment')
    x_is_not_payment = fields.Boolean('Not Payment')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_accountant_payment_line_id = fields.Many2one('account.payment.line', 'Accountant Payment Line')
    x_accountant_payment_tax_id = fields.Many2one('account.payment.tax', 'Accountant Payment Tax')