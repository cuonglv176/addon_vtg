# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _, tools

_logger = logging.getLogger(__name__)


class VTGRportSaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_for_sale = fields.Monetary(string='Doanh thu được tính', store=True, compute='_amount_for_sale', tracking=4)

    def write(self, vals):
        for sale_id in self:
            amount_for_sale = 0.0
            for line in sale_id.order_line:
                if sale_id.type_order in ('cod', 'ship'):
                    if line.product_id.categ_id.id in (1, 2, 3, 4, 13) and sale_id.status_transfer != 'return':
                        amount_for_sale += line.price_subtotal
                else:
                    if line.product_id.categ_id.id in (1, 2, 13) and sale_id.status_transfer != 'return':
                        amount_for_sale += line.price_subtotal
                    elif line.user_id.id == sale_id.user_id.id and sale_id.status_transfer != 'return':
                        amount_for_sale += line.price_subtotal
            vals.update({
                'amount_for_sale': amount_for_sale,
            })
            res = super(VTGRportSaleOrder, self).write(vals)
            return res

    @api.depends('order_line.price_total', 'type_order', 'order_line.user_id')
    def _amount_for_sale(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_for_sale = 0.0
            for line in order.order_line:
                if order.type_order in ('cod', 'ship'):
                    if line.product_id.categ_id.id in (1, 2, 3, 4, 13) and order.status_transfer != 'return':
                        amount_for_sale += line.price_subtotal
                else:
                    if line.product_id.categ_id.id in (1, 2, 13) and order.status_transfer != 'return':
                        amount_for_sale += line.price_subtotal
                    elif line.user_id.id == order.user_id.id and order.status_transfer != 'return':
                        amount_for_sale += line.price_subtotal
            order.update({
                'amount_for_sale': amount_for_sale,
            })


class VTGRportSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def write(self, vals):
        for line_id in self:
            user_id = line_id.user_id.id
            res = super(VTGRportSaleOrderLine, self).write(vals)
            user_new_id = line_id.user_id.id
            if user_id != user_new_id:
                amount_for_sale = 0.0
                for line in line_id.order_id.order_line:
                    if line_id.order_id.type_order in ('cod', 'ship'):
                        if line.product_id.categ_id.id in (
                        1, 2, 3, 4, 13) and line_id.order_id.status_transfer != 'return':
                            amount_for_sale += line.price_subtotal
                    else:
                        if line.product_id.categ_id.id in (1, 2, 13) and line_id.order_id.status_transfer != 'return':
                            amount_for_sale += line.price_subtotal
                        elif line.user_id.id == line_id.order_id.user_id.id and line_id.order_id.status_transfer != 'return':
                            amount_for_sale += line.price_subtotal
                line_id.order_id.update({
                    'amount_for_sale': amount_for_sale,
                })
            return res
