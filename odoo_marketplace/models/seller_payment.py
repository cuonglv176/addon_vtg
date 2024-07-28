# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, AccessError
import datetime

import logging
_logger = logging.getLogger(__name__)


class SellerPayment(models.Model):
    _name = 'seller.payment'
    _inherit = ['mail.thread']
    _description = "Seller Payment"
    _order = 'date desc, id desc'

    @api.model
    def _get_mp_currency(self):
        return self.env['ir.default'].get('res.config.settings', 'mp_currency_id') or self.env.user.company_id.currency_id

    def _check_all_move_line_status(self):
        for rec in self:
            flag = False
            if rec.payment_mode == "order_paid":
                if rec.memo:
                    stock_move_objs = self.env["stock.move"].search(
                        [('origin', '=', rec.memo), ('product_id.marketplace_seller_id', '=', rec.seller_id.id)])
                    if all(move.state == 'done' for move in stock_move_objs):
                        flag = True
                if not flag and rec.invoice_id:
                    flag = True
            rec.is_cashable = flag

    def _make_it_searchable(self, operator, value):
        self.env.cr.execute("""SELECT id FROM seller_payment""")
        all_seller_payment_ids = []
        ids = []
        for dic in self.env.cr.dictfetchall():
            all_seller_payment_ids.append(dic["id"])
        for obj in self.sudo().browse(all_seller_payment_ids):
            if obj.is_cashable:
                ids.append(obj.id)
        return [('id', 'in', ids)]

    name = fields.Char(string="Record Reference",
                       default="NEW", translate=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    state = fields.Selection([("draft", "Draft"), ("requested", "Requested/Validated"),
                              ("confirm", "Confirmed"), ("posted", "Paid"), ("canceled", "Cancelled")], default="draft", copy=False, tracking=True)
    seller_id = fields.Many2one("res.partner", string="Seller", domain=[
                                ('seller', '=', True)], required=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    payment_method = fields.Many2one("seller.payment.method", string="Payment Method",
                                     help="Payment method in which mode you want payment from vendor.", copy=False)
    date = fields.Date(
        string="Payment Date", default=fields.Date.context_today, required=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    description = fields.Text(string="Payment Description",  translate=True, copy=False)
    payment_type = fields.Selection([('cr', 'Credit'), ('dr', 'Debit')], default="cr", string="Type",
                                    help="Credit means vendor will pay you & debit means vendor has been paid. ", readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    payment_mode = fields.Selection([('order_paid', 'Order Paid'), ('order_refund', 'Order Refund'), (
        'seller_payment', 'Seller Payment')], string="Payment Mode", required=True, default="order_paid", readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True, states={
                                 'draft': [('readonly', False)]}, copy=False)
    payable_amount = fields.Float(string="Payable Amount", required=True,
                                  help="Positive amount means vendor will pay to seller & negative amount means vendor has been paid/or seller have to refund.", readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    memo = fields.Char(string="Memo", copy=False)
    is_cashable = fields.Boolean(compute="_check_all_move_line_status", string="Cashable", search='_make_it_searchable',
                                 help="If all delivery releted to the order have been delivered then seller will be able to get payment.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id, readonly=True)
    invoice_currency_id = fields.Many2one('res.currency', string="Invoice Currency", compute="_set_invoice_currency", store=True, tracking=True)
    currency_id = fields.Many2one("res.currency", string="Marketplace Currency", default=_get_mp_currency,tracking=True, required="1", readonly="1")
    invoiced_amount = fields.Monetary(string='Seller Amount in seller Currency', currency_field='invoice_currency_id',
        readonly=True)
    invoice_line_ids = fields.Many2many("account.move.line", "seller_paymnet_invoice_line", "seller_payment", "account_invoice_line", "Invoice Lines", readonly="1")
    seller_commission = fields.Float("Applied Commission", compute="_set_seller_commission", store=True, tracking=True, compute_sudo=True)

    @api.model
    def _read_group_fill_results( self, domain, groupby, remaining_groupbys,
        aggregated_fields, count_field,read_group_result, read_group_order=None):

        if groupby == 'state':
            for result in read_group_result:
                state = result['state']
                if state in ["confirm","posted","canceled"]:
                    result['__fold'] = True
        return super(SellerPayment, self)._read_group_fill_results(domain, groupby, remaining_groupbys,
            aggregated_fields, count_field, read_group_result, read_group_order)

    @api.depends("invoice_id", "invoice_id.currency_id")
    def _set_invoice_currency(self):
        self.invoice_currency_id = self.invoice_id.currency_id or self.env['ir.default'].get('res.config.settings', 'mp_currency_id') or self.env.user.company_id.currency_id

    # @api.depends("company_id", "company_id.currency_id")
    # def _set_mp_currency(self):
    #     self.currency_id = self.env['ir.default'].get('res.config.settings', 'mp_currency_id') or self.env.user.company_id.currency_id

    @api.depends("seller_id")
    def _set_seller_commission(self):
        for rec in self:
            rec.seller_commission = rec.seller_id.get_seller_global_fields('commission') if rec.seller_id else 0.0

    @api.onchange("payment_type")
    def onchange_payment_type(self):
        if self.payment_type == "dr":
            self.payable_amount = -abs(self.payable_amount)
            self.payment_mode = "seller_payment"
        else:
            self.payable_amount = abs(self.payable_amount)
            self.payment_mode = "order_paid"

    @api.onchange("payment_mode")
    def onchange_payment_mode(self):
        if self.payment_mode in ["seller_payment", "order_refund"]:
            self.payment_type = "dr"
        else:
            self.payment_type = "cr"

    @api.model
    def validate_on_create(self, vals):
        # Code For validation
        seller_obj = self.env["res.partner"].browse(vals.get("seller_id"))
        if seller_obj and vals.get("payment_mode", False) == "seller_payment" and vals.get("payment_type", False) == "dr":
            seller_pending_payment_obj = self.search([("seller_id", "=", seller_obj.id), ("state", "in", [
                                                     "requested", "confirm"]), ("payment_mode", "=", "seller_payment")], limit=1)
            if seller_pending_payment_obj:
                raise ValidationError(
                    _("This seller already has a pending request of payment."))
            seller_payment_obj = self.search(
                [("seller_id", "=", seller_obj.id), ("state", "=", "posted")], limit=1)
            seller_payment_limit = seller_obj.get_seller_global_fields('seller_payment_limit')
            if seller_payment_obj:
                last_payment_date = datetime.datetime.strptime(
                    str(seller_payment_obj.date), '%Y-%m-%d').date()
                today_date = datetime.datetime.today().date()
                days_diff = today_date - last_payment_date
                if days_diff.days >= seller_obj.get_seller_global_fields('next_payment_request') and abs(vals["payable_amount"]) >= seller_payment_limit and abs(vals["payable_amount"]) <= seller_obj.cashable_amount:
                    pass
                else:
                    raise ValidationError(
                        _("Seller is not eligible for payment request.... "))
            else:
                if abs(vals["payable_amount"]) >= seller_payment_limit and abs(vals["payable_amount"]) <= seller_obj.cashable_amount:
                    pass
                else:
                    raise ValidationError(
                        _("Seller is not eligible for payment request.... "))
        return vals

    def action_invoice_register_payment(self):
        return self.env['account.payment']\
            .with_context(active_ids=self.ids, active_model='seller.payment', active_id=self.id)\
            .action_register_payment()


    @api.model
    def create(self, vals):
        if not self._context.get("pass_create_validation"):
            vals = self.validate_on_create(vals)
        if vals.get('payment_mode') == 'order_paid':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'seller.order.payment') or 'NEW INV'
        if vals.get('payment_mode') == 'order_refund':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'seller.order.refund') or 'NEW REF'
            invoice_obj = self.env["account.move"].search(
                [("name", "=", vals.get("memo"))])
            # Not a good way to do this
            seller_payment_objs = self.search(
                [("invoice_id", "=", invoice_obj.id), ("seller_id", "=", vals.get("seller_id"))])
            seller_payment_objs.write({"state": "canceled"})
            vals["state"] = "canceled"
        if vals.get('payment_mode') == 'seller_payment':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'seller.payment') or 'NEW PAY'
        if vals.get('payment_type') == 'dr':
            vals['payable_amount'] = -abs(vals['payable_amount'])
        #This is for resolving error:a partner cannot follow twice the same object
        if vals.get("message_follower_ids", False):
            vals.pop("message_follower_ids")
        res = super(SellerPayment, self).create(vals)
        return res

    def write(self, vals):
        res = False
        if vals.get("payable_amount", False) or vals.get("payment_type", False):
            for rec in self:
                if rec.payment_type and vals.get("payment_type", False) and rec.payment_type != vals.get("payment_type", False):
                    raise ValidationError(_('You can no change Type of paymnet. Create new seller paymnet for it.'))
                payable_amount = vals.get("payable_amount", False) or rec.payable_amount
                payment_type = vals.get("payment_type", False) or rec.payment_type
                if payment_type == 'dr':
                    vals.update({'payable_amount': -abs(payable_amount)})
                else:
                    vals.update({'payable_amount': abs(payable_amount)})
                res = super(SellerPayment, rec).write(vals)
        else:
            res = super(SellerPayment, self).write(vals)
        return res

    def unlink(self):
        for paymnet in self:
            if paymnet.state not in ('draft', 'canceled'):
                raise ValidationError(_('You can delete only draft or cancelled paymnet! Try to cancel it before.'))
        return super(SellerPayment, self).unlink()

    def change_seller_id(self, seller_id):
        result = {}
        if seller_id:
            partner_obj = self.env['res.partner'].browse(seller_id)
            payment_method = partner_obj.payment_method
            if payment_method:
                ids = payment_method.ids
                result['domain'] = {'payment_method': [('id', 'in', ids)]}
                return result
            else:
                raise ValidationError(
                    _("Seller has no payment method. Please assign payment method to seller."))
        else:
            return result

    def do_validate(self):
        for rec in self:
            if rec.payment_type == "cr":
                rec.state = "requested"

            if rec.payment_type == "dr":
                seller_pending_payment_obj = self.search([("seller_id", "=", rec.seller_id.id), ("state", "in", [
                                                         "requested", "confirm"]), ("payment_mode", "=", "seller_payment")], limit=1)
                if seller_pending_payment_obj:
                    raise ValidationError(
                        _("This seller already has a pending request of payment."))
                seller_payment_obj = self.search(
                    [("seller_id", "=", rec.seller_id.id), ("state", "=", "posted")], limit=1)
                seller_payment_limit = rec.seller_id.get_seller_global_fields('seller_payment_limit')
                if seller_payment_obj:
                    last_payment_date = datetime.datetime.strptime(
                        str(seller_payment_obj.date), '%Y-%m-%d').date()
                    today_date = datetime.datetime.today().date()
                    days_diff = today_date - last_payment_date
                    if days_diff.days >= rec.seller_id.get_seller_global_fields('next_payment_request') and abs(rec.payable_amount) >= seller_payment_limit and abs(rec.payable_amount) <= rec.seller_id.cashable_amount:
                        rec.state = "requested"
                    else:
                        raise ValidationError(
                            _("Not eligible for payment request.... "))
                else:
                    if abs(rec.payable_amount) >= seller_payment_limit and abs(rec.payable_amount) <= rec.seller_id.cashable_amount:
                        rec.state = "requested"
                    else:
                        raise ValidationError(
                            _("You are not eligible for payment request now.... "))

    def do_Confirm(self):
        for rec in self:
            resConfig = self.env['res.config.settings']
            if rec.payment_type == "dr":
                invoice_type = "in_invoice"
                seller_journal_id = resConfig.get_mp_global_field_value("seller_payment_journal_id")
                if seller_journal_id:
                    journal_ids = self.env['account.journal'].browse([seller_journal_id])
                else:
                    journal_ids = self.env['account.journal'].search(
                        [('type', '=', 'purchase'), ('company_id', '=', rec.seller_id.company_id.id)], limit=1)
            else:
                invoice_type = "out_invoice"
                journal_ids = self.env['account.journal'].search(
                        [('type', '=', 'sale'), ('company_id', '=', rec.seller_id.company_id.id)], limit=1)

            product_id = resConfig.get_mp_global_field_value("seller_payment_product_id")

            invoice_line_vals = {
                "name": _("Seller Payment"),
                "product_id": product_id,
                # "account_id": rec.seller_id.property_account_payable_id.id,
                "quantity": 1,
                "price_unit": abs(rec.payable_amount),
                "currency_id": rec.currency_id.id,
            }
            default_term = self.env.ref('account.account_payment_term_immediate').id
            invoice_vals = {
                "move_type": "in_invoice",
                "partner_id": rec.seller_id.id,
                "journal_id": journal_ids[0].id if journal_ids else False,
                "invoice_origin": rec.name,
                "currency_id": rec.currency_id.id,
                "invoice_date": rec.date,
                "mp_seller_bill": True,
                "invoice_payment_term_id": default_term,
                "invoice_line_ids": [(0,0,invoice_line_vals)],
            }
            created_invoice_obj = self.env["account.move"].sudo().with_context(default_type='in_invoice', default_display_name='Seller Bill', default_invoice_payment_term_id=default_term).create(invoice_vals)
            if created_invoice_obj:
                rec.write({
                    "invoice_line_ids": [(6, 0, created_invoice_obj.invoice_line_ids.ids)],
                    "invoice_id": created_invoice_obj.id,
                    "invoiced_amount": created_invoice_obj.amount_total,
                    "state":"confirm",
                })

    def view_invoice(self):
        action = self.env.ref('account.action_move_out_invoice_type').sudo().read()[0]
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = self.invoice_id.id
        action['context'] = {
            "is_seller": True
        }
        return action

    def do_Confirm_and_view_invoice(self):
        self.ensure_one()
        self.do_Confirm()
        return self.view_invoice()

    @api.depends('invoice_id.state')
    def change_seller_payment_state(self):
        for rec in self:
            if rec.payment_mode == "seller_payment" and rec.invoice_id.state == "paid":
                rec.state = "posted"

    def do_paid(self):
        for rec in self:
            rec.invoice_id.signal_workflow("invoice_open")
            rec.state = "posted"

    def copy(self, default=None):
        raise ValidationError(_("You can not duplicate seller paymnet."))

    def pay_to_seller(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'seller.payment.wizard',
            'binding_view_types': 'form',
            'view_mode': 'form',
            'res_id': 'id_of_the_wizard',
            'target': 'new',
        }
