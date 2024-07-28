# -*- coding: utf-8 -*-
import logging
import pytz
from odoo import fields, models, api, _
from datetime import date, datetime, timezone, timedelta
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

ones = ["", "một ", "hai ", "ba ", "bốn ", "năm ", "sáu ", "bảy ", "tám ", "chín ", "mười ", "mười một ", "mười hai ",
        "mười ba ", "mười bốn ", "mười lăm ", "mười sáu ", "mười bảy ", "mười tám ", "mười chín "]
twenties = ["", "", "hai mươi ", "ba mươi ", "bốn mươi ", "năm mươi ", "sáu mươi ", "bảy mươi ", "tám mươi ",
            "chín mươi "]
thousands = ["", "nghìn ", "triệu ", "tỉ ", "nghìn ", "triệu ", "tỉ "]


def num999(n, next):
    c = n % 10  # singles digit
    b = int(((n % 100) - c) / 10)  # tens digit
    a = int(((n % 1000) - (b * 10) - c) / 100)  # hundreds digit
    t = ""
    h = ""
    if a != 0 and b == 0 and c == 0:
        t = ones[a] + "trăm "
    elif a != 0:
        t = ones[a] + "trăm "
    elif a == 0 and b == 0 and c == 0:
        t = ""
    elif a == 0 and next != '':
        t = "không trăm "
    if b == 1:
        h = ones[n % 100]
    if b == 0:
        if a > 0 and c > 0:
            h = "linh " + ones[n % 100]
        else:
            h = ones[n % 100]
    elif b > 1:
        if c == 4:
            tmp = "tư "
        elif c == 1:
            tmp = "mốt "
        else:
            tmp = ones[c]
        h = twenties[b] + tmp
    st = t + h
    return st


def num2word(num):
    if not isinstance(num, int):
        raise ValidationError("Number to convert to words must be integer")
    if num == 0: return 'không'
    i = 3
    n = str(num)
    word = ""
    k = 0
    while (i == 3):
        nw = n[-i:]
        n = n[:-i]
        int_nw = int(float(nw))
        if int_nw == 0:
            word = num999(int_nw, n) + thousands[int_nw] + word
        else:
            word = num999(int_nw, n) + thousands[k] + word
        if n == '':
            i += 1
        k += 1
    return word[:-1].capitalize()


class AccountPaymentCash(models.Model):
    _name = 'account.payment.cash.bank'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default=lambda self: _('New'), copy=False)
    payment_type = fields.Selection([
        ('cash_in', 'Cash In'),
        ('cash_out', 'Cash Out'),
        ('bank_in', 'Bank In'),
        ('bank_out', 'Bank Out'),
    ], default='cash_in', string="Payment Type")
    description = fields.Text(string='Description', tracking=True)
    payment_date = fields.Date('Payment Date', default=date.today(), tracking=True)
    payment_lines = fields.One2many('account.payment.line', 'payment_id', 'Payment Lines', copy=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    rate_id = fields.Many2one('res.currency.rate', string='Rate', tracking=True)
    rate = fields.Float(related='rate_id.rate', string='Rate', tracking=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    amount_total = fields.Float('Amount Total', compute='_compute_amount_total')
    amount_before_tax = fields.Monetary(string='Payment Amount before tax', store=True, compute='_amount_before_tax')
    amount_tax = fields.Monetary(string='Payment Amount Tax', store=True, compute='_amount_tax')

    move_ids = fields.One2many('account.move', 'x_payment_option_id', string="Account Moves", track_visibility='always')
    tax_lines = fields.One2many('account.payment.tax', 'payment_id', 'Tax Lines', copy=True)
    count_move = fields.Integer('Count Move', compute='_compute_count_move')
    journal_id = fields.Many2one('account.journal', string='Journal', tracking=True)
    credit_account_id = fields.Many2one('account.account', related='journal_id.default_account_id')
    debit_account_id = fields.Many2one('account.account', related='journal_id.default_account_id')

    bank_id = fields.Many2one('res.bank', 'Bank')
    partner_bank_id = fields.Many2one('res.partner.bank', 'Bank account')
    receiver = fields.Char('Receiver')
    partner_id = fields.Many2one('res.partner', 'Partner')
    address = fields.Char('Address')
    ref = fields.Char('Ref', required=True, readonly=True)

    x_time_print = fields.Char(string="Date Time Print")
    x_time_confirm = fields.Char(string="Date Time Confirm")

    bill_move_ids = fields.Many2many('account.move', 'payment_bill_move', 'move_id', 'payment_id',
                                     string="Account Move One Bill")

    @api.onchange('partner_id')
    def onchange_domain_partner_bank_id(self):
        if self.partner_id:
            self.address = self.partner_id.street
            self.ref = self.partner_id.ref
            bank_ids = self.partner_id.bank_ids
            if bank_ids:
                return {'domain': {'partner_bank_id': [('id', 'in', bank_ids.ids)]}}
            else:
                return {'domain': {'partner_bank_id': [(0, '=', 1)]}}
        else:
            return {'domain': {'partner_bank_id': [(1, '=', 1)]}}

    @api.depends('move_ids')
    def _compute_count_move(self):
        for item in self:
            item.count_move = len(item.move_ids.ids)

    @api.depends('amount_before_tax', 'amount_tax')
    def _compute_amount_total(self):
        for item in self:
            item.amount_total = item.amount_before_tax + item.amount_tax

    @api.depends('payment_lines.value')
    def _amount_before_tax(self):
        for item in self:
            item.amount_before_tax = sum(x.value for x in item.payment_lines)

    @api.depends('tax_lines.amount_tax')
    def _amount_tax(self):
        for item in self:
            item.amount_tax = sum(x.amount_tax for x in item.tax_lines)

    @api.model
    def create(self, vals):
        if self._context.get('default_payment_type') == 'cash_in':
            vals['name'] = self.env['ir.sequence'].next_by_code('cash.in')
        if self._context.get('default_payment_type') == 'cash_out':
            vals['name'] = self.env['ir.sequence'].next_by_code('cash.out')
        if self._context.get('default_payment_type') == 'bank_in':
            vals['name'] = self.env['ir.sequence'].next_by_code('bank.in')
        if self._context.get('default_payment_type') == 'bank_out':
            vals['name'] = self.env['ir.sequence'].next_by_code('bank.out')
        return super(AccountPaymentCash, self).create(vals)

    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise UserError(_("You cannot delete record if the state is not 'Draft'."))
            for line in item.payment_lines:
                line.unlink()
        return super(AccountPaymentCash, self).unlink()

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            if self._context.get('default_payment_type') in ['cash_in', 'bank_in']:
                debit_account_id = self.journal_id.payment_debit_account_id.id
                for line in self.payment_lines:
                    line.debit_account_id = debit_account_id
            if self._context.get('default_payment_type') in ['cash_out', 'bank_out']:
                credit_account_id = self.journal_id.payment_credit_account_id.id
                for line in self.payment_lines:
                    line.credit_account_id = credit_account_id
            if self.journal_id.type == 'bank':
                self.bank_id = self.journal_id.bank_id.id
                # self.partner_bank_id = self.journal_id.bank_account_id.id
        else:
            self.bank_id = False
            self.partner_bank_id = False

    @api.onchange('currency_id')
    def onchange_currency(self):
        if not self.currency_id:
            self.rate_id = False
        if self.currency_id:
            for line in self.payment_lines:
                line.currency_id = self.currency_id
                line.rate = self.rate
                line.value_natural_currency = line.value * line.rate

    def action_view_move(self):
        action = self.env.ref('account.action_move_journal_line')
        result = action.sudo().read()[0]
        result['domain'] = "[('id', 'in', " + str(self.move_ids.ids) + ")]"
        result[
            'context'] = "{'default_move_type': 'entry', 'view_no_maturity': True, 'create': False, 'delete': False, 'edit': False}"
        return result

    def _create_move_entry(self):
        context_payment_type = self.payment_type
        if context_payment_type in ('cash_out', 'bank_out'):
            move_lines = []
            for line in self.payment_lines:
                if line.value <= 0:
                    raise UserError(_("Total amount must be greater than 0"))
                amount = line.value_natural_currency if line.value_natural_currency != 0 else line.value
                debit_move_vals = {
                    'name': line.name,
                    'ref': self.name,
                    'date': self.payment_date,
                    'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else None,
                    'x_account_expense_item_id': line.account_expense_item_id.id if line.account_expense_item_id else None,
                    'account_id': line.debit_account_id.id,
                    'debit': amount,
                    'credit': 0,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id,
                    'x_accountant_payment_line_id': line.id
                }
                if self.currency_id.id != self.company_id.currency_id.id:
                    debit_move_vals['currency_id'] = self.currency_id.id
                    debit_move_vals['amount_currency'] = line.value
                if line.debit_account_id.user_type_id.type in ('receivable', 'payable'):
                    debit_move_vals['date_maturity'] = self.payment_date
                move_lines.append((0, 0, debit_move_vals))

                # thu chi công ty
                credit_move_vals = {
                    'name': line.name,
                    'ref': self.name,
                    'date': self.payment_date,
                    'account_id': self.journal_id.payment_credit_account_id.id,
                    'debit': 0,
                    'credit': amount,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id,
                    'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else None,
                    'x_account_expense_item_id': line.account_expense_item_id.id if line.account_expense_item_id else None,
                    'x_accountant_payment_line_id': line.id
                }
                if self.journal_id.payment_credit_account_id.user_type_id.type in ('receivable', 'payable'):
                    credit_move_vals['date_maturity'] = self.payment_date
                move_lines.append((0, 0, credit_move_vals))
            if len(self.tax_lines) > 0:
                payment_line_id = self.env['account.payment.line'].search([('payment_id', '=', self.id)], limit=1)
                amount = 0
                for tax in self.tax_lines:
                    if tax.amount_tax > 0:
                        # Ghi sổ trả/nhận của các đối tác
                        debit_move_vals = {
                            'name': tax.name,
                            'ref': tax.name,
                            'date': self.payment_date,
                            'account_id': tax.account_tax_id.id,
                            'debit': tax.amount_tax,
                            'credit': 0.0,
                            'partner_id': tax.partner_id.id,
                            'x_accountant_payment_tax_id': tax.id
                        }
                        move_lines.append((0, 0, debit_move_vals))

                        # Ghi sổ thu/chi của công ty
                        credit_move_vals = {
                            'ref': tax.name,
                            'name': tax.name,
                            'date': self.payment_date,
                            'account_id': payment_line_id.credit_account_id.id,
                            'debit': 0.0,
                            'credit': tax.amount_tax,
                            'partner_id': tax.partner_id.id,
                            'x_accountant_payment_tax_id': tax.id
                        }
                        move_lines.append((0, 0, credit_move_vals))
                    elif tax.amount_tax < 0:
                        # Ghi sổ trả/nhận của các đối tác
                        debit_move_vals = {
                            'name': tax.name,
                            'ref': tax.name,
                            'date': self.payment_date,
                            'account_id': payment_line_id.credit_account_id.id,
                            'debit': tax.amount_tax,
                            'credit': 0.0,
                            'partner_id': tax.partner_id.id,
                            'x_accountant_payment_tax_id': tax.id
                        }
                        move_lines.append((0, 0, debit_move_vals))

                        # Ghi sổ thu/chi của công ty
                        credit_move_vals = {
                            'ref': tax.name,
                            'name': tax.name,
                            'date': self.payment_date,
                            'account_id': tax.account_tax_id.id,
                            'debit': 0.0,
                            'credit': tax.amount_tax,
                            'partner_id': tax.partner_id.id,
                            'x_accountant_payment_tax_id': tax.id
                        }
                        move_lines.append((0, 0, credit_move_vals))
            move_vals = {
                'ref': self.name,
                'date': self.payment_date,
                'journal_id': self.journal_id.id,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'line_ids': move_lines,
                'x_payment_option_id': self.id,
                'name': self.name
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            move_id.name = self.name

        if context_payment_type in ('cash_in', 'bank_in'):
            move_lines = []
            for line in self.payment_lines:
                if line.value <= 0:
                    raise UserError(_("Total amount must be greater than 0"))
                amount = line.value_natural_currency if line.value_natural_currency != 0 else line.value
                credit_move_vals = {
                    'name': line.name,
                    'ref': self.name,
                    'date': self.payment_date,
                    'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else None,
                    'x_account_expense_item_id': line.account_expense_item_id.id if line.account_expense_item_id else None,
                    'account_id': line.credit_account_id.id,
                    'debit': 0,
                    'credit': amount,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id,
                    'x_accountant_payment_line_id': line.id
                }
                if line.credit_account_id.user_type_id.type in ('receivable', 'payable'):
                    credit_move_vals['date_maturity'] = self.payment_date
                if self.currency_id.id != self.company_id.currency_id.id:
                    credit_move_vals['currency_id'] = self.currency_id.id
                    credit_move_vals['amount_currency'] = line.value
                move_lines.append((0, 0, credit_move_vals))

                # thu chi công ty
                debit_move_vals = {
                    'name': line.name,
                    'ref': self.name,
                    'date': self.payment_date,
                    'account_id': self.journal_id.payment_debit_account_id.id,
                    'debit': amount,
                    'credit': 0,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id,
                    'analytic_account_id': line.analytic_account_id.id if line.analytic_account_id else None,
                    'x_account_expense_item_id': line.account_expense_item_id.id if line.account_expense_item_id else None,
                    'x_accountant_payment_line_id': line.id
                }
                if self.journal_id.payment_debit_account_id.user_type_id.type in ('receivable', 'payable'):
                    debit_move_vals['date_maturity'] = self.payment_date
                move_lines.append((0, 0, debit_move_vals))
            move_vals = {
                'ref': self.name,
                'date': self.payment_date,
                'journal_id': self.journal_id.id,
                'partner_id': self.partner_id.id if self.partner_id else False,
                'line_ids': move_lines,
                'x_payment_option_id': self.id,
                'name': self.name
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            move_id.name = self.name

    def action_posted(self):
        try:
            if self.state == 'posted':
                raise UserError(_("Record has been posted! Refresh your browser, please"))
            if len(self.payment_lines) == 0:
                raise UserError(_("You do not have accounting details, please check again!"))
            for move_id in self.move_ids:
                move_id.button_cancel()
                move_id.with_context(force_delete=True).unlink()
            self._create_move_entry()
            self.state = 'posted'
            tz = pytz.timezone(self.env.user.tz) or pytz.utc
            date = pytz.utc.localize(
                datetime.strptime(datetime.strftime(datetime.now(), '%d/%m/%Y %H:%M:%S'),
                                  '%d/%m/%Y %H:%M:%S')).astimezone(tz)
            self.x_time_confirm = datetime.strftime(date, '%d/%m/%Y %H:%M:%S')
            if self.payment_type in ('cash_out', 'bank_out'):
                for line in self.payment_lines:
                    if line.debit_account_id.id == self.partner_id.property_account_payable_id.id:
                        if not self.bill_move_ids:
                            self.action_supplier_payment(line.debit_account_id)
                        else:
                            move_id = self.env['account.move'].search([('id', 'in', self.bill_move_ids.ids)])
                            self.action_supplier_payment_one_bill(line.debit_account_id, move_id.ids)
            else:
                for line in self.payment_lines:
                    if line.credit_account_id == self.partner_id.property_account_payable_id:
                        if not self.bill_move_ids:
                            self.action_supply_payment_return(line.credit_account_id)
                        else:
                            move_id = self.env['account.move'].search([('id', 'in', self.bill_move_ids.ids)])
                            self.action_supply_payment_return_bills(line.credit_account_id, move_id.ids)
        except Exception as e:
            raise ValidationError(e)

    def action_draft(self):
        ''' posted -> draft '''
        for move_id in self.move_ids:
            move_id.button_draft()
            move_id.with_context(force_delete=True).unlink()
        if not self.move_ids:
            self.state = 'draft'

    def action_cancel(self):
        ''' posted -> draft '''
        for move_id in self.move_ids:
            move_id.button_cancel()
        if all([move_id.state == 'cancel' for move_id in self.move_ids]):
            self.state = 'cancel'

    def action_supplier_payment(self, account_id):
        try:
            if self.partner_id.supplier_rank >= 1:
                move_line_debit_ids = self.env['account.move.line'].search(
                    [('debit', '>', 0), ('parent_state', '=', 'posted'), ('reconciled', '=', False),
                     ('amount_residual', '>', 0),
                     ('partner_id', '=', self.partner_id.id), ('account_id', '=', account_id.id)])
                if move_line_debit_ids:
                    for move_line_debit in move_line_debit_ids:
                        move_line_credit_ids = self.env['account.move.line'].search(
                            [('credit', '>', 0), ('parent_state', '=', 'posted'),
                             ('partner_id', '=', self.partner_id.id),
                             ('reconciled', '=', False), ('amount_residual', '<', 0),
                             ('account_id', '=', account_id.id), ('move_id.x_is_not_payment', '=', False)],
                            order='date asc')
                        if move_line_credit_ids:
                            for move_line_credit in move_line_credit_ids:
                                if move_line_debit.reconciled:
                                    break
                                if move_line_credit.reconciled:
                                    break
                                move_line_credit.move_id.js_assign_outstanding_line(move_line_debit.id)
                                if move_line_debit.amount_residual == 0:
                                    continue

        except Exception as e:
            raise ValidationError(e)

    def action_supplier_payment_one_bill(self, account_id, move_ids):
        try:
            if self.partner_id.supplier_rank >= 1:
                move_line_debit_ids = self.env['account.move.line'].search(
                    [('debit', '>', 0), ('parent_state', '=', 'posted'), ('reconciled', '=', False),
                     ('amount_residual', '>', 0),
                     ('partner_id', '=', self.partner_id.id), ('account_id', '=', account_id.id)])
                if move_line_debit_ids:
                    for move_line_debit in move_line_debit_ids:
                        move_line_credit_ids = self.env['account.move.line'].search(
                            [('credit', '>', 0), ('parent_state', '=', 'posted'),
                             ('partner_id', '=', self.partner_id.id),
                             ('reconciled', '=', False), ('amount_residual', '<', 0),
                             ('account_id', '=', account_id.id), ('move_id.x_is_not_payment', '=', False),
                             ('move_id', 'in', move_ids)], order='date asc')
                        if move_line_credit_ids:
                            for move_line_credit in move_line_credit_ids:
                                if move_line_debit.reconciled:
                                    break
                                if move_line_credit.reconciled:
                                    break
                                move_line_credit.move_id.js_assign_outstanding_line(move_line_debit.id)
                                if move_line_debit.amount_residual == 0:
                                    continue

        except Exception as e:
            raise ValidationError(e)

    def action_print(self):
        url = 'report/pdf/ev_account_cash_bank.report_account_cash_bank/%s' % (self.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
            'res_id': self.id,
        }

    def action_print_bank_in_out(self):
        tz = pytz.timezone(self.env.user.tz) or pytz.utc
        date = pytz.utc.localize(
            datetime.strptime(datetime.strftime(datetime.now(), '%d/%m/%Y %H:%M:%S'), '%d/%m/%Y %H:%M:%S')).astimezone(
            tz)
        self.x_time_print = datetime.strftime(date, '%d/%m/%Y %H:%M:%S')
        url = 'report/pdf/ev_account_cash_bank.report_account_bank_in_out/%s' % (self.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
            'res_id': self.id,
        }

    def action_supply_payment_return(self, account_id):
        try:
            if self.partner_id.supplier_rank >= 1:
                move_line_credit_ids = self.env['account.move.line'].search(
                    [('credit', '>', 0), ('parent_state', '=', 'posted'), ('reconciled', '=', False),
                     ('amount_residual', '<', 0),
                     ('partner_id', '=', self.partner_id.id), ('account_id', '=', account_id.id)])
                if move_line_credit_ids:
                    for move_line_credit in move_line_credit_ids:
                        move_line_debit_ids = self.env['account.move.line'].search(
                            [('debit', '>', 0), ('parent_state', '=', 'posted'),
                             ('partner_id', '=', self.partner_id.id),
                             ('reconciled', '=', False), ('amount_residual', '>', 0),
                             ('account_id', '=', account_id.id), ('move_id.x_is_not_payment', '=', False)],
                            order='date asc')
                        if move_line_debit_ids:
                            for move_line_debit in move_line_debit_ids:
                                if move_line_debit.reconciled:
                                    break
                                if move_line_debit.reconciled:
                                    break
                                move_line_debit.move_id.js_assign_outstanding_line(move_line_credit.id)
                                if move_line_debit.amount_residual == 0:
                                    break

        except Exception as e:
            raise ValidationError(e)

    def action_supply_payment_return_bills(self, account_id, move_ids):
        try:
            if self.partner_id.supplier_rank >= 1:
                move_line_credit_ids = self.env['account.move.line'].search(
                    [('credit', '>', 0), ('parent_state', '=', 'posted'), ('reconciled', '=', False),
                     ('amount_residual', '<', 0),
                     ('partner_id', '=', self.partner_id.id), ('account_id', '=', account_id.id)])
                if move_line_credit_ids:
                    for move_line_credit in move_line_credit_ids:
                        move_line_debit_ids = self.env['account.move.line'].search(
                            [('debit', '>', 0), ('parent_state', '=', 'posted'),
                             ('partner_id', '=', self.partner_id.id),
                             ('reconciled', '=', False), ('amount_residual', '>', 0),
                             ('account_id', '=', account_id.id), ('move_id.x_is_not_payment', '=', False),
                             ('move_id', 'in', move_ids)],
                            order='date asc')
                        if move_line_debit_ids:
                            for move_line_debit in move_line_debit_ids:
                                if move_line_debit.reconciled:
                                    break
                                if move_line_debit.reconciled:
                                    break
                                move_line_debit.move_id.js_assign_outstanding_line(move_line_credit.id)
                                if move_line_debit.amount_residual == 0:
                                    break

        except Exception as e:
            raise ValidationError(e)

    def get_amount_word(self, amount):
        res = num2word(int(amount)) + " đồng chẵn."
        return res


class PartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def name_get(self):
        result = []
        for record in self:
            name = record.acc_number
            if record.bank_name:
                name = record.acc_number + ' ' + record.bank_name
            result.append((record.id, name))
        return result
