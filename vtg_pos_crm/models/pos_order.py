# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
import pytz


class PosOrder(models.Model):
    _inherit = 'pos.order'

    booking_id = fields.Many2one('crm.lead.booking', 'Booking')
    marketing_id = fields.Many2one('res.users', 'Marketing')
    department_id = fields.Many2one('hr.department', 'Department')
    source_id = fields.Many2one('utm.source', string='Nguồn')

    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh', compute="depends_channel_id", store=True,
                                 track_visibility='onchange')

    @api.depends('source_id')
    def depends_channel_id(self):
        for s in self:
            if s.source_id:
                s.channel_id = s.source_id.channel_id

    @api.model
    def _process_order(self, order, draft, existing_order):
        pos_id = super(PosOrder, self)._process_order(order, draft, existing_order)
        if not pos_id:
            return pos_id
        pos = self.env['pos.order'].browse(pos_id)
        if not pos.partner_id:
            return pos_id
        try:
            booking_id = order['data'].get('booking', {}).get('id', None)
        except:
            booking_id = None
        if not booking_id:
            return pos_id
        booking_id = self.env['crm.lead.booking'].browse(booking_id)
        if not booking_id:
            return pos_id
        pos.booking_id = booking_id.id
        pos.user_id = booking_id.user_id.id
        pos.crm_team_id = booking_id.team_id.id
        pos.marketing_id = booking_id.marketing_id.id
        pos.department_id = booking_id.department_id.id
        pos.account_move.invoice_user_id = booking_id.user_id.id
        pos.account_move.marketing_id = booking_id.marketing_id.id
        pos.account_move.department_id = booking_id.department_id.id
        return pos_id

    def _prepare_invoice_vals(self):
        self.ensure_one()
        timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        if self.booking_id:
            user_id = self.booking_id.user_id
        else:
            user_id = self.user_id
        vals = {
            'invoice_origin': self.name,
            'journal_id': self.session_id.config_id.invoice_journal_id.id,
            'move_type': 'out_invoice' if self.amount_total >= 0 else 'out_refund',
            'ref': self.name,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self._get_partner_bank_id(),
            # considering partner's sale pricelist's currency
            'currency_id': self.pricelist_id.currency_id.id,
            'invoice_user_id': user_id.id,
            'marketing_id': self.marketing_id.id,
            'department_id': self.department_id.id,
            'invoice_date': self.date_order.astimezone(timezone).date(),
            'fiscal_position_id': self.fiscal_position_id.id,
            'invoice_line_ids': self._prepare_invoice_lines(),
            'invoice_payment_term_id': self.partner_id.property_payment_term_id.id or False,
            'invoice_cash_rounding_id': self.config_id.rounding_method.id
            if self.config_id.cash_rounding and (not self.config_id.only_round_cash_method or any(
                p.payment_method_id.is_cash_count for p in self.payment_ids))
            else False
        }
        if self.note:
            vals.update({'narration': self.note})
        return vals


    @api.model
    def create(self, vals):
        if vals.get('booking_id'):
            booking_id = self.env['crm.lead.booking'].browse(vals['booking_id'])
            vals.update({
                'user_id': booking_id.user_id.id,
                'department_id': booking_id.user_id.employee_id.department_id.id,
                'marketing_id': booking_id.marketing_id.id,
                'source_id': booking_id.source_id.id,
            })
        else:
            vals.update({
                'source_id': 29,
            })
        order_id = super(PosOrder, self).create(vals)
        return order_id
