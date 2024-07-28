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
import dateutil
from datetime import datetime

from odoo import models, fields, api, _
from odoo.addons.website_sale_stock.models.sale_order import SaleOrder as WebsiteSaleStock
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_cancel(self):
        result = super(SaleOrder,self).action_cancel()
        for rec in self:
            if rec.state == 'cancel' and rec.order_line:
                mp_order_line = rec.order_line.filtered(lambda line: line.marketplace_seller_id != False)
                if mp_order_line:
                    mp_order_line.write({'marketplace_state':'cancel'})
        return result

    def action_draft(self):
        result = super(SaleOrder,self).action_draft()
        for rec in self:
            if rec.state == 'draft' and rec.order_line:
                mp_order_line = rec.order_line.filtered(lambda line: line.marketplace_seller_id != False)
                if mp_order_line:
                    mp_order_line.write({'marketplace_state':'new'})
        return result

    def get_seller_product_list(self, seller):
        self.ensure_one()
        product_list = []
        if seller:
            product_list = self.order_line.mapped('product_id').filtered(lambda l: l.marketplace_seller_id.id == seller.id).mapped('name')
        return ', '.join(product_list)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        """ Mark Marketplace state in Pending """
        for rec in self:
            if rec.order_line:
                mp_order_line = rec.order_line.filtered(lambda line: line.marketplace_seller_id != False)
                if mp_order_line:
                    mp_order_line.write({'marketplace_state':'pending'})
        resConfig = self.env['res.config.settings']
        if resConfig.get_mp_global_field_value("enable_notify_seller_on_new_order"):
            temp_id = resConfig.get_mp_global_field_value("notify_seller_on_new_order_m_tmpl_id")
            if temp_id:
                template_obj = self.env['mail.template'].browse(temp_id)
                for order in self:
                    seller_objs = order.order_line.mapped('marketplace_seller_id')
                    for seller in seller_objs:
                        template_obj.with_context(seller=seller).with_company(self.env.company).send_mail(order.id, True)
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.order_id.name))
        return result

    marketplace_seller_id = fields.Many2one(
        related='product_id.marketplace_seller_id', string='Marketplace Seller', store=True, copy=False)
    marketplace_state = fields.Selection([("new","New"),("pending","Pending"), ("approved","Approved") , ("shipped","Shipped"), ("cancel","Cancelled")], default="new", copy=False)
    mp_delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_seller_picking_ids')

    order_carrier_id = fields.Many2one("delivery.carrier", related="order_id.carrier_id", string="Delivery Method")
    create_year = fields.Integer("Create Year",compute='_compute_create_year',store=True)
    seller_amount = fields.Float("Seller Amount", readonly=True)
    admin_commission = fields.Float("Admin Commission", readonly=True)

    @api.model
    def _read_group_fill_results( self, domain, groupby, remaining_groupbys,
        aggregated_fields, count_field,read_group_result, read_group_order=None):

        if groupby == 'marketplace_state':
            for result in read_group_result:
                state = result['marketplace_state']
                if state in ['cancel','shipped']:
                    result['__fold'] = True
        return super(SaleOrderLine, self)._read_group_fill_results(domain, groupby, remaining_groupbys,
            aggregated_fields, count_field, read_group_result, read_group_order)

    @api.depends('create_date')
    def _compute_create_year(self):
        for sol in self:
            sol.create_year = sol.create_date.year

    @api.depends('order_id.procurement_group_id')
    def _compute_seller_picking_ids(self):
        for sol in self:
            sol.mp_delivery_count = len(sol.mapped('order_id.picking_ids').filtered(lambda picking: picking.marketplace_seller_id.id == sol.marketplace_seller_id.id))

    def action_view_delivery(self):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env.ref('odoo_marketplace.marketplace_stock_picking_action').sudo().read()[0]

        pickings = self.mapped('order_id.picking_ids').filtered(lambda picking: picking.marketplace_seller_id.id == self.marketplace_seller_id.id)
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            action['views'] = [(self.env.ref('odoo_marketplace.marketplace_picking_stock_modified_form_view').id, 'form')]
            action['res_id'] = pickings.id
        return action

    def action_view_sol_seller_payment(self):
        self.ensure_one()
        seller_payment_objs = self.order_id.invoice_ids.mapped('seller_payment_ids').filtered(lambda sp: sp.seller_id.id == self.marketplace_seller_id.id)
        action = self.env.ref('odoo_marketplace.wk_seller_payment_action').sudo().read()[0]
        if len(seller_payment_objs) > 1:
            action['domain'] = [('id', 'in', seller_payment_objs.ids)]
        elif len(seller_payment_objs) == 1:
            action['views'] = [(self.env.ref('odoo_marketplace.wk_seller_payment_form_view').id, 'form')]
            action['res_id'] = seller_payment_objs.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def button_cancel(self):
        for rec in self:
            pickings = rec.mapped('order_id.picking_ids').filtered(lambda picking: picking.marketplace_seller_id.id == rec.marketplace_seller_id.id)
            pickings.action_cancel()
            rec.sudo().marketplace_state = "cancel"

    def confirm_sale_order_line(self):
        for rec in self:
            if rec.order_id.state == 'sale':
                rec.write({'marketplace_state':'pending'})
            else:
                rec.order_id.action_confirm()

    def button_sale_order_cancel(self):
        for rec in self:
            rec.order_id.action_cancel()


    def button_approve_ol(self):
        for rec in self:
            if rec.product_id.type == 'service':
                rec.sudo().marketplace_state = "shipped"
            else:
                rec.sudo().marketplace_state = "approved"

    def button_ship_ol(self):
        for rec in self:
            move_objs = self.env["stock.move"].sudo().search([('origin','=',rec.sudo().order_id.name), ('product_id','=', rec.product_id.id)],limit=1)
            for move_obj in move_objs:
                move_obj.action_done()
                if move_obj.state == "done":
                    rec.sudo().marketplace_state = "shipped"
                else:
                    raise Warning(_("Not able to done delivery order for this order. Please check the available quantity of the product. "))

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        self.ensure_one()
        marketplace_seller_obj = self.marketplace_seller_id
        if marketplace_seller_obj:
            seller_warehouse_id = marketplace_seller_obj.get_seller_global_fields('warehouse_id')
            if seller_warehouse_id:
                seller_warehouse_obj = self.env['stock.warehouse'].browse(seller_warehouse_id)
                values["warehouse_id"] = seller_warehouse_obj
        return values

def new_cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
    values = super(WebsiteSaleStock, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
    line_id = values.get('line_id')

    for line in self.order_line:
        if  not line.product_id.allow_out_of_stock_order:
            if line.product_id.marketplace_seller_id and line.product_id.type == 'product':
                warehouse_id = self.warehouse_id.id
                seller_obj = line.marketplace_seller_id
                if seller_obj:
                    seller_warehouse_id = seller_obj.get_seller_global_fields("warehouse_id")
                    if seller_warehouse_id:
                        warehouse_id = seller_warehouse_id
                cart_qty = sum(self.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                available_qty = line.product_id.with_context(warehouse=warehouse_id).virtual_available
                if cart_qty > available_qty and (line_id == line.id):
                    mp_qty = available_qty - cart_qty
                    new_val = super(WebsiteSaleStock, self)._cart_update(line.product_id.id, line.id, mp_qty, 0, **kwargs)
                    values.update(new_val)

                    # Make sure line still exists, it may have been deleted in super()_cartupdate because mp_qty can be <= 0
                    if line.exists() and new_val['quantity']:
                        line.warning_stock = _('You ask for %s products but only %s is available') % (cart_qty, new_val['quantity'])
                        values['warning'] = line.warning_stock
                    else:
                        self.warning_stock = _("Some products became unavailable and your cart has been updated. We're sorry for the inconvenience.")
                        values['warning'] = self.warning_stock
            else:
                cart_qty = sum(self.order_line.filtered(lambda p: p.product_id.id == line.product_id.id).mapped('product_uom_qty'))
                if cart_qty > line.product_id.with_context(warehouse=self.warehouse_id.id).free_qty and (line_id == line.id):
                    qty = line.product_id.with_context(warehouse=self.warehouse_id.id).free_qty - cart_qty
                    new_val = super(SaleOrder, self)._cart_update(line.product_id.id, line.id, qty, 0, **kwargs)
                    values.update(new_val)

                    # Make sure line still exists, it may have been deleted in super()_cartupdate because qty can be <= 0
                    if line.exists() and new_val['quantity']:
                        line.warning_stock = _('You ask for %s products but only %s is available') % (cart_qty, new_val['quantity'])
                        values['warning'] = line.warning_stock
                    else:
                        self.warning_stock = _("Some products became unavailable and your cart has been updated. We're sorry for the inconvenience.")
                        values['warning'] = self.warning_stock
    return values

WebsiteSaleStock._cart_update = new_cart_update
