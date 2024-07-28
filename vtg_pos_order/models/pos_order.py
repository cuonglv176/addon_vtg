# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'


    def _get_fields_for_order_line(self):
        fields = super(PosOrder, self)._get_fields_for_order_line()
        fields.extend([
            'user_id',
            'user_master_id',
            'user_assistant_id',
        ])
        return fields

    amount_for_sale = fields.Monetary(string='Doanh thu được tính', store=True, compute='_amount_for_sale', tracking=4)
    type_customer = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', default='new')

    # def unlink(self):
    #     partner_id = self.partner_id
    #     res = super(PosOrder, self).unlink()
    #     self.auto_update_type_customer(partner_id)
    #     return res

    # @api.model
    # def create(self, vals):
    #     order_id = super(PosOrder, self).create(vals)
    #     order_id.auto_update_type_customer(order_id.partner_id)
    #     return
    #
    #
    # def auto_update_type_customer(self, partner_id):
    #     if partner_id:
    #         order_ids = self.env['pos.order'].sudo().search(
    #             [('partner_id', '=', partner_id.id), ('state', 'in', ('paid','done','invoiced'))])
    #         for sale in order_ids:
    #             order = self.env['pos.order'].sudo().search(
    #                 [('partner_id', '=', sale.partner_id.id), ('date_order', '<', sale.date_order),
    #                  ('state', 'in', ('paid','done','invoiced'))])
    #             if order:
    #                 if order.lines:
    #                     a = 0
    #                     for order_id in order_ids:
    #                         for line in order_id.lines:
    #                             if line.product_id.categ_id.id == 1:
    #                                 a = 1
    #                     if a == 1:
    #                         sale.type_customer = 'old'
    #                     else:
    #                         sale.type_customer = 'new'
    #                 else:
    #                     sale.type_customer = 'new'
    #             else:
    #                 sale.type_customer = 'new'

    @api.depends('lines')
    def _amount_for_sale(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_for_sale = 0.0
            for line in order.lines:
                if line.product_id.categ_id.id in (1, 2, 13) :
                    amount_for_sale += line.price_subtotal
            order.update({
                'amount_for_sale': amount_for_sale,
            })


class AccountMove(models.Model):
    _inherit = 'account.move'

    pos_order_id = fields.Many2one('pos.order', string='Tham chiếu đơn hàng POS', compute="_get_pos_order", store=True)

    @api.depends('pos_order_ids')
    def _get_pos_order(self):
        for s in self:
            for order_id in s.pos_order_ids:
                s.pos_order_id = order_id