# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        # _create_payments đang sinh ra account.move.line đối soát cho bill
        # payments = self._create_payments()
        move_id = 0
        ids = []
        if self.partner_id:
            for line in self.line_ids:
                if line.move_id.x_is_not_payment == True:
                    raise UserError(_("Invoices are not allowed to payments."))
                ids.append(line.move_id.id)
                move_id = line.move_id
            if not self.partner_id.ref:
                raise UserError(_('Partner is not Ref'))

            move_ids = self.env['account.move'].search([('id', 'in', ids)])
            payments = self._create_account_payment_cash_bank(self.partner_id, self.journal_id, move_ids,
                                                              move_id.move_type)
        else:
            raise UserError(_("you can payments for multiple invoices with the same supplier."))

        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.cash.bank',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        # else:
        #     action.update({
        #         'view_mode': 'tree,form',
        #         'domain': [('id', 'in', payments.ids)],
        #     })
        return action

    def _create_account_payment_cash_bank(self, partner_id, journal_id, move_ids, type):
        try:
            account_payment_cash_bank = self.env['account.payment.cash.bank']
            description = _('Pay for bill: ') + self.communication
            account_id = partner_id.property_account_payable_id
            if type != 'in_refund':
                if self.journal_id.type == 'cash':
                    account_payment_cash_bank = self.env['account.payment.cash.bank'].with_context(
                        {'default_payment_type': 'cash_out'}).create({
                        'partner_id': partner_id.id,
                        'ref': partner_id.ref,
                        'receiver': partner_id.name,
                        'address': partner_id.street,
                        'payment_date': self.payment_date,
                        'journal_id': journal_id.id,
                        'payment_type': 'cash_out',
                        'description': description,
                        'bill_move_ids': move_ids.ids,
                    })
                elif self.journal_id.type == 'bank':
                    account_payment_cash_bank = self.env['account.payment.cash.bank'].with_context(
                        {'default_payment_type': 'bank_out'}).create({
                        'partner_id': partner_id.id,
                        'ref': partner_id.ref,
                        'receiver': partner_id.name,
                        'address': partner_id.street,
                        'payment_date': self.payment_date,
                        'journal_id': journal_id.id,
                        'payment_type': 'bank_out',
                        'description': description,
                        'partner_bank_id': self.partner_bank_id.id,
                        'bill_move_ids': move_ids.ids,
                    })
                account_payment_line = self.env['account.payment.line'].create({
                    'payment_id': account_payment_cash_bank.id,
                    'name': description,
                    'debit_account_id': account_id.id,
                    'credit_account_id': self.journal_id.default_account_id.id,
                    'value': self.amount,
                    'value_natural_currency': self.amount,
                })
            else:
                if self.journal_id.type == 'cash':
                    account_payment_cash_bank = self.env['account.payment.cash.bank'].with_context(
                        {'default_payment_type': 'cash_in'}).create({
                        'partner_id': partner_id.id,
                        'ref': partner_id.ref,
                        'receiver': partner_id.name,
                        'address': partner_id.street,
                        'payment_date': self.payment_date,
                        'journal_id': journal_id.id,
                        'payment_type': 'cash_in',
                        'description': description,
                        'bill_move_ids': move_ids.ids,
                    })
                elif self.journal_id.type == 'bank':
                    account_payment_cash_bank = self.env['account.payment.cash.bank'].with_context(
                        {'default_payment_type': 'bank_in'}).create({
                        'partner_id': partner_id.id,
                        'ref': partner_id.ref,
                        'receiver': partner_id.name,
                        'address': partner_id.street,
                        'payment_date': self.payment_date,
                        'journal_id': journal_id.id,
                        'payment_type': 'bank_in',
                        'description': description,
                        'partner_bank_id': self.partner_bank_id.id,
                        'bill_move_ids': move_ids.ids,
                    })
                account_payment_line = self.env['account.payment.line'].create({
                    'payment_id': account_payment_cash_bank.id,
                    'name': description,
                    'debit_account_id': self.journal_id.default_account_id.id,
                    'credit_account_id': account_id.id,
                    'value': self.amount,
                    'value_natural_currency': self.amount,
                })


            account_payment_cash_bank.action_posted()
            return account_payment_cash_bank

        except Exception as e:
            raise ValidationError(e)
