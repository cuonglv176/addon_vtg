# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons.sale_stock.models.sale_order import SaleOrderLine
from odoo.tools import float_compare, float_round


def _action_launch_stock_rule(self, previous_product_uom_qty=False):
    """
    Launch procurement group run method with required/custom fields genrated by a
    sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
    depending on the sale order line product rule.
    """
    if self._context.get("skip_procurement"):
        return True
    precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    procurements = []
    for line in self:
        line = line.with_company(line.company_id)
        if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
            continue
        qty = line._get_qty_procurement(previous_product_uom_qty)
        if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
            continue

        group_id = line._get_procurement_group()
        if not group_id:
            group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
            line.order_id.procurement_group_id = group_id
        else:
            # In case the procurement group is already created and the order was
            # cancelled, we need to update certain values of the group.
            updated_vals = {}
            if group_id.partner_id != line.order_id.partner_shipping_id:
                updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
            if group_id.move_type != line.order_id.picking_policy:
                updated_vals.update({'move_type': line.order_id.picking_policy})
            if updated_vals:
                group_id.write(updated_vals)

        values = line._prepare_procurement_values(group_id=group_id)
        product_qty = line.product_uom_qty - qty

        line_uom = line.product_uom
        quant_uom = line.product_id.uom_id
        product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
        procurements.append(self.env['procurement.group'].Procurement(
            line.product_id, product_qty, procurement_uom,
            line.order_id.partner_shipping_id.property_stock_customer,
            line.product_id.display_name, line.order_id.name, line.order_id.company_id, values))
    if procurements:
        self.env['procurement.group'].run(procurements)

    # This next block is currently needed only because the scheduler trigger is done by picking confirmation rather than stock.move confirmation
    orders = self.mapped('order_id')
    for order in orders:
        order.picking_ids.update({'x_sale_user_id': order.user_id.id})
        pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])

        # tuuh edit
        for move_id in pickings_to_confirm.move_ids_without_package:
            parent_location_id = move_id.location_id.location_id
            if not parent_location_id:
                continue
            pushaway_rule_id = self.env['stock.pushaway.rule'].sudo().search(
                [('location_in_id', '=', parent_location_id.id),
                 '|',
                    '&', ('product_id', '!=', False), ('product_id', '=', move_id.product_id.id),
                    '&', ('category_id', '!=', False), ('category_id', '=', move_id.product_id.categ_id.id)
                 ], order='sequence')
            if not pushaway_rule_id:
                continue
            move_id.location_id = pushaway_rule_id.location_out_id.id
            for line in move_id.move_line_ids:
                line.location_id = pushaway_rule_id.location_out_id.id
        if pickings_to_confirm:
            # Trigger the Scheduler for Pickings
            pickings_to_confirm.action_confirm()
    return True


SaleOrderLine._action_launch_stock_rule = _action_launch_stock_rule
