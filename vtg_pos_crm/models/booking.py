# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api, _


class CRM_Booking(models.Model):
    _inherit = 'crm.lead.booking'

    pos_order_count = fields.Integer('POS Order Count', compute="_compute_pos_order_count")

    def _compute_pos_order_count(self):
        for item in self:
            item.pos_order_count = self.env['pos.order'].sudo().search_count([('booking_id', '=', item.id)])

    def action_view_pos(self):
        action = self.env.ref('point_of_sale.action_pos_pos_form').read()[0]
        if action.get('domain', ''):
            action['domain'] = str(eval(action['domain']) + [('booking_id', '=', self.id)])
        return action

    @api.depends('state')
    def _compute_status_customer(self):
        res = super(CRM_Booking, self)._compute_status_customer()
        for item in self:
            if item.state and (len(item.sale_ids) > 0 or item.pos_order_count > 0):
                item.status_customer = 'buy'
        return res
