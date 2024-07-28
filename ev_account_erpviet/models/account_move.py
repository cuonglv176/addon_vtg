# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from collections import defaultdict
from dateutil.relativedelta import relativedelta


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    x_number_invoice = fields.Char('Number Invoice', states={"draft": [("readonly", False)]}, copy=False)
    x_code_invoice = fields.Char('Code Invoice', states={"draft": [("readonly", False)]}, copy=False)
    x_invoice_form = fields.Char('Invoice Form', states={"draft": [("readonly", False)]}, copy=False)
    x_address = fields.Char('Address', related='partner_id.street', copy=False)
    x_vat = fields.Char('VAT', related='partner_id.vat', copy=False)
    journal_general_ids = fields.One2many('account.journal.general', 'account_move_id', 'Journal general', ondelete='cascade')

    def _set_args_journal_general(self, debit, credit, default=True, amountt=0):
        if amountt != 0:
            amount = amountt
        else:
            amount = debit.debit if default else credit.credit
        return {
            'name': debit.name,
            'debit_partner_id': debit.partner_id.id,
            'credit_partner_id': credit.partner_id.id,
            'journal_id': self.journal_id.id,
            'debit_acc_id': debit.account_id.id,
            'credit_acc_id': credit.account_id.id,
            'product_id': debit.product_id.id if default else credit.product_id.id,
            'uom_id': debit.product_uom_id.id if default else credit.product_uom_id.id,
            'qty': debit.quantity if default else credit.quantity,
            'value': amount,
            'date': self.date,
            'state': 'posted',
            'account_move_id': self.id,
            'company_id': debit.company_id.id,
            'debit_analytic_account_id': debit.analytic_account_id.id,
            'credit_analytic_account_id': credit.analytic_account_id.id,
            'analytic_tag_ids': debit.analytic_tag_ids,
            'amount_currency': debit.amount_currency if default else credit.amount_currency,
            'company_currency_id': debit.company_currency_id.id,
            'currency_id': debit.currency_id.id if default else credit.currency_id.id,
        }

    def _sync_journal_general(self, debit, credit, amountt=0):
        if len(debit) == 1 and len(credit) == 1:
            args_journal_general = self._set_args_journal_general(debit[0], credit[0], True, amountt)
            journal_general_id = self.env['account.journal.general'].create(args_journal_general)
            debit[0].x_journal_general_id = journal_general_id.id
            credit[0].x_journal_general_id = journal_general_id.id
            return True
        if len(debit) > 1:
            for line in debit:
                args_journal_general = self._set_args_journal_general(line, credit[0], True)
                journal_general_id = self.env['account.journal.general'].create(args_journal_general)
                line.x_journal_general_id = journal_general_id.id
        else:
            for line in credit:
                args_journal_general = self._set_args_journal_general(debit[0], line, False)
                journal_general_id = self.env['account.journal.general'].create(args_journal_general)
                line.x_journal_general_id = journal_general_id.id
        return True

    def _update_contra_account_id(self):
        debit = []
        credit = []
        if self.stock_move_id:
            if self.stock_move_id._is_out():
                for line in self.line_ids:
                    if line.account_id.id != line.product_id.categ_id.property_stock_valuation_account_id.id:
                        debit.append(line)
                    elif line.account_id.id == line.product_id.categ_id.property_stock_valuation_account_id.id:
                        credit.append(line)
            elif self.stock_move_id._is_in():
                for line in self.line_ids:
                    if line.account_id.id == line.product_id.categ_id.property_stock_valuation_account_id.id:
                        debit.append(line)
                    elif line.account_id.id != line.product_id.categ_id.property_stock_valuation_account_id.id:
                        credit.append(line)
            else:
                for line in self.line_ids:
                    if line.debit > 0:
                        debit.append(line)
                    elif line.credit > 0:
                        credit.append(line)
        else:
            for line in self.line_ids:
                if line.debit > 0:
                    debit.append(line)
                elif line.credit > 0:
                    credit.append(line)

        if len(debit) > 1 and len(credit) > 1:
            list_debit = []
            list_credit = []
            for d in debit:
                if d.id in list_debit:
                    continue
                amount = d.debit
                for c in credit:
                    if c.id in list_credit:
                        continue
                    if amount == 0:
                        break
                    if c.credit < amount:
                        list_credit.append(c.id)
                        c.contra_account_id = d.account_id.id
                        self._sync_journal_general(d, c, c.credit)
                        amount -= c.credit
                    elif c.credit == amount:
                        list_credit.append(c.id)
                        list_debit.append(d.id)
                        c.contra_account_id = d.account_id.id
                        d.contra_account_id = c.account_id.id
                        self._sync_journal_general(d, c, c.credit)
                        amount = 0
                    else:
                        list_debit.append(d.id)
                        d.contra_account_id = c.account_id.id
                        self._sync_journal_general(d, c, amount)
                        amount = 0
            return True

        if len(debit) == 0 or len(credit) == 0:
            return True

        if len(debit) == 1 and len(credit) == 1:
            debit[0].contra_account_id = credit[0].account_id.id
            debit[0].x_financial_report = True
            credit[0].contra_account_id = debit[0].account_id.id
            credit[0].x_financial_report = False
            self._sync_journal_general(debit, credit)
            return True

        if len(debit) > 1:
            self._sync_journal_general(debit, credit)
            credit = credit[0]
            credit.contra_account_id = False
            credit.x_financial_report = False
            for line in debit:
                line.contra_account_id = credit.account_id.id
                line.x_financial_report = True
        else:
            self._sync_journal_general(debit, credit)
            debit = debit[0]
            debit.contra_account_id = False
            debit.x_financial_report = False
            for line in credit:
                line.contra_account_id = debit.account_id.id
                line.x_financial_report = True
        return True

    def _post(self, soft=True):
        result = super(AccountMoveInherit, self)._post(soft)
        for item in self:
            account_posting = self.env['account.posting'].search([('account_move_id', '=', item.id)])
            if not account_posting:
                item._check_required_account()
            item._check_time_allow()
            item._update_contra_account_id()
            for line in item.line_ids:
                if line.purchase_line_id:
                    item.update_stock_move_value(line.purchase_line_id)
                if line.move_id.move_type == 'in_invoice' or line.move_id.move_type == 'in_refund' or line.move_id.x_accountant_bill_id:
                    line.x_type_transfer = 'in'
                if line.move_id.stock_move_id.picking_id.pos_session_id:
                    line.x_type_transfer = 'out'
        return result

    def update_stock_move_value(self, purchase_line_id):
        account_move_line = self.env['account.move.line'].search([('parent_state','=','posted'),('purchase_line_id','=',purchase_line_id.id)])
        amount = 0
        for move_line in account_move_line:
            amount += move_line.price_subtotal
        stock_move = self.env['stock.move'].search([('purchase_line_id','=',purchase_line_id.id),('state','=','done')])
        qty = 0
        for move in stock_move:
            qty += move.product_uom_qty
        if qty != 0:
            price_unit = amount/qty
            if purchase_line_id.order_id.x_is_return == True:
                sql = """
                    UPDATE stock_move 
                    SET x_unit_cost = %s, x_value = -(product_uom_qty * %s)
                    WHERE
                    purchase_line_id = %s;
                    UPDATE stock_move_line a 
                    SET x_unit_cost = %s, x_value = -(qty_done * %s)
                    FROM stock_move b
                    WHERE
                    a.move_id = b.id and 
                    b.purchase_line_id = %s;
                    UPDATE stock_valuation_layer a 
                    SET unit_cost = %s, value = -(quantity * %s)
                    FROM stock_move b
                    WHERE
                    a.stock_move_id = b.id and 
                    b.purchase_line_id = %s;
                """
                self._cr.execute(sql % (price_unit, price_unit, purchase_line_id.id, price_unit, price_unit, purchase_line_id.id, price_unit, price_unit, purchase_line_id.id))
            else:
                sql = """
                    UPDATE stock_move 
                    SET x_unit_cost = %s, x_value = (product_uom_qty * %s)
                    WHERE
                    purchase_line_id = %s;
                    
                    UPDATE stock_move_line a 
                    SET x_unit_cost = %s, x_value = (qty_done * %s)
                    FROM stock_move b
                    WHERE
                    a.move_id = b.id and 
                    b.purchase_line_id = %s;
                    
                    UPDATE stock_valuation_layer a 
                    SET unit_cost = %s, value = (quantity * %s)
                    FROM stock_move b
                    WHERE
                    a.stock_move_id = b.id and 
                    b.purchase_line_id = %s;
                """
                self._cr.execute(
                    sql % (price_unit, price_unit, purchase_line_id.id, price_unit, price_unit, purchase_line_id.id, price_unit, price_unit, purchase_line_id.id))

    def _check_time_allow(self):
        if self.company_id.x_allow_record_account_move:
            date_allow_pre = self.create_date.date() - relativedelta(days=self.company_id.x_allow_record_account_move)
            date_allow_nxt = self.create_date.date() + relativedelta(days=self.company_id.x_allow_record_account_move)
            if self.date < date_allow_pre or self.date > date_allow_nxt:
                raise UserError("Bạn không thể vào sổ. Do đã quá ngày cho phép chỉnh sửa")

    def _check_required_account(self):
        for line_id in self.line_ids:
            if line_id.account_id.x_required_product and not line_id.product_id:
                raise UserError("%s: Bạn không thể vào sổ. Do tài khoản %s bắt buộc nhập sẩn phẩm" % (self.name,line_id.account_id.code))
            if line_id.account_id.x_required_analytic and not line_id.analytic_account_id:
                raise UserError("%s: Bạn không thể vào sổ. Do tài khoản %s bắt buộc nhập bộ phận chịu phí" % (self.name,line_id.account_id.code))
            if line_id.account_id.x_required_expense_item and not line_id.x_account_expense_item_id:
                raise UserError("%s: Bạn không thể vào sổ. Do tài khoản %s bắt buộc nhập khoản mục phí" % (self.name,line_id.account_id.code))
            if line_id.account_id.x_required_partner and not line_id.partner_id:
                raise UserError("%s: Bạn không thể vào sổ. Do tài khoản %s bắt buộc nhập đối tượng" % (self.name,line_id.account_id.code))

    def button_cancel(self):
        result = super(AccountMoveInherit, self).button_cancel()
        for move in self:
            move.journal_general_ids.unlink()
            for line in move.line_ids:
                line.contra_account_id = False
                line.x_financial_report = False
        return result

    def button_draft(self):
        result = super(AccountMoveInherit, self).button_draft()
        for move in self:
            move._check_time_allow()
            move.journal_general_ids.unlink()
            for line in move.line_ids:
                line.contra_account_id = False
                line.x_financial_report = False
        return result

    #re-define _compute_name
    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        for item in self:
            if (item.posted_before and item.name != '/') or item.state == 'draft':
                continue

            today = fields.Date.today()
            journal_code = item.journal_id.code
            prefix = f'{journal_code}{today.year - 2000:02d}{today.month:02d}{today.day:02d}/'
            domain = [('name', 'like', prefix)]
            if item.journal_id.id:
                domain.append(('journal_id', '=', item.journal_id.id))
            if item.move_type:
                domain.append(('move_type', '=', item.move_type))
            if item.id:
                domain.append(('id', '!=', item.id))
            lasted_id = self.search(domain, limit=1, order='name desc')
            if lasted_id:
                highest_name = lasted_id.name
                new_num = f'{int(highest_name.split("/")[-1]) + 1:05d}'
            else:
                new_num = '00001'
            item.name = f'{prefix}{new_num}'
        self.filtered(lambda m: not m.name).name = '/'

    @api.constrains('line_ids')
    def _constraint_partner_and_analytic_in_line(self):
        for item in self:
            if item.company_id.id != 2:
                continue
            for line in item.line_ids:
                if line.account_id.code in ('131', '1311', '331', '3311'):
                    if not line.partner_id:
                        raise UserError(
                            _("Partner is not null to Account receivable or payable!"))
                if line.account_id.is_required_analytic and line.debit != 0:
                    if not line.analytic_account_id:
                        raise UserError(
                            _("Analytic is not null to Account expense!"))

    def name_get(self):
        result = []
        for move in self:
            ref = ''
            if move.move_type != 'entry':
                ref = move.name
            else:
                if move.payment_id:
                    if move.payment_id.partner_type == 'customer':
                        ref = f'Thanh toán của KH - {move.name}'
                    else:
                        ref = f'Thanh toán cho NCC - {move.name}'
                else:
                    ref = move.ref if move.ref else move.name
            result.append((move.id, ref))
        return result
