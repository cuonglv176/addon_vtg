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

from odoo import models, fields, api, _, SUPERUSER_ID
from lxml import etree
from datetime import datetime, timedelta
import odoo.addons.decimal_precision as dp
from odoo.tools.translate import _
from odoo.exceptions import except_orm, ValidationError, RedirectWarning
from .mp_tools import *
import logging
_logger = logging.getLogger(__name__)


class MarketplaceStock(models.Model):
    _name = "marketplace.stock"
    _inherit = ['mail.thread']
    _description = "Marketplace Stock"

    @api.model
    def _set_product_template(self):
        if self._context.get('active_model') == 'product.template':
            product_id = self.env['product.template'].browse(
                self._context.get('active_id'))
            return product_id.id
        else:
            product_id = self.env['product.product'].browse(
                self._context.get('active_id'))
            return product_id.product_tmpl_id.id if product_id else False
        seller_group = self.env['ir.model.data'].check_object_reference(
            'odoo_marketplace', 'marketplace_seller_group')[1]
        officer_group = self.env['ir.model.data'].check_object_reference(
            'odoo_marketplace', 'marketplace_officer_group')[1]
        groups_ids = self.env.user.sudo().groups_id.ids
        if seller_group in groups_ids and officer_group not in groups_ids:
            marketplace_seller_id = self.env.user.sudo().partner_id.id
            domain = {'product_temp_id':  [
                ('marketplace_seller_id', '=', marketplace_seller_id)]}
            return {'domain': domain}
        return self.env['product.template']

    @api.model
    def _set_product_id(self):
        if self._context.get('active_model') == 'product.template':
            product_ids = self.env['product.product'].search(
                [('product_tmpl_id', '=', self._context.get('active_id'))])
            return self.env['product.product'].browse(product_ids.ids[0]).id
        else:
            product_obj = self.env['product.product'].search([('id', '=', self._context.get('active_id'))])
            if product_obj:
                return product_obj.id


    @api.model
    def _get_product_location(self):
        if self._context.get('active_model') == 'product.template':
            product_ids = self.env['product.product'].search(
                [('product_tmpl_id', '=', self._context.get('active_id'))])
            product_obj = product_ids[0]
        else:
            product_obj = self.env['product.product'].search([('id', '=', self._context.get('active_id'))])
        if product_obj:
            if product_obj.location_id:
                return product_obj.location_id.id
            else:
                return product_obj.marketplace_seller_id.get_seller_global_fields('location_id')

    @api.model
    def _set_title(self):
        msg = "Stock added on "
        current_date = datetime.today().strftime('%d-%B-%Y')
        title = msg + current_date
        return title

    name = fields.Char(string="Title", default=_set_title,
                       required=True,  translate=True)
    product_temp_id = fields.Many2one(
        'product.template', string='Product Template', default=_set_product_template)
    product_id = fields.Many2one(
        'product.product', string='Product', default=_set_product_id)
    marketplace_seller_id = fields.Many2one(
        "res.partner", related="product_id.marketplace_seller_id", string="Seller", store=True)
    new_quantity = fields.Float('New Quantity on Hand', default=1, digits='Product Unit of Measure', required=True, help='This quantity is expressed in the Default Unit of Measure of the product.', copy=False)
    location_id = fields.Many2one(
        'stock.location', 'Location', required=True, default=_get_product_location)
    state = fields.Selection([("draft", "Draft"), ("requested", "Requested"), (
        "approved", "Approved"), ("rejected", "Rejected")], string="Status", default="draft", copy=False)
    note = fields.Text("Notes",  translate=True)
    product_variant_count = fields.Integer('Variant Count', related='product_temp_id.product_variant_count')

    @api.model
    def _read_group_fill_results( self, domain, groupby, remaining_groupbys,
        aggregated_fields, count_field,read_group_result, read_group_order=None):

        if groupby == 'state':
            for result in read_group_result:
                state = result['state']
                if state in ["approved", "rejected"]:
                    result['__fold'] = True
        return super(MarketplaceStock, self)._read_group_fill_results(domain, groupby, remaining_groupbys,
            aggregated_fields, count_field, read_group_result, read_group_order)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(MarketplaceStock, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        seller_group = self.env['ir.model.data'].check_object_reference(
            'odoo_marketplace', 'marketplace_seller_group')[1]
        officer_group = self.env['ir.model.data'].check_object_reference(
            'odoo_marketplace', 'marketplace_officer_group')[1]
        groups_ids = self.env.user.sudo().groups_id.ids
        if seller_group in groups_ids and officer_group not in groups_ids:
            marketplace_seller_id = self.env.user.sudo().partner_id.id

            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='product_temp_id']"):
                node.set(
                    'domain', "[('type', '=', 'product'), ('status','=','approved'),('marketplace_seller_id', '=', %s)]" % marketplace_seller_id)
            for node in doc.xpath("//field[@name='product_id']"):
                node.set(
                    'domain', "[('type', '=', 'product'), ('status','=','approved'),('marketplace_seller_id', '=', %s)]" % marketplace_seller_id)
            res['arch'] = etree.tostring(doc)
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.ensure_one()
        if self.product_id:
            self.product_temp_id = self.product_id.product_tmpl_id.id
            self.location_id = self.product_id.marketplace_seller_id.get_seller_global_fields('location_id') or False,

    @check_mp_officer
    def approve(self):
        self._approve()

    def _approve(self):
        for obj in self:
            if obj.state == "requested" and obj.product_id.status == "approved" and obj.product_id.marketplace_seller_id.state == "approved":
                obj.change_product_qty()
                obj.write({"state": "approved"})
            else:
                _logger.info("-------- MP inventory request can not be approved. Inventory request not in requested state or product is not approved or product seller is not approved. ----------")

    @check_mp_officer
    def reject(self):
        for obj in self:
            if obj.state == "requested":
                obj.write({"state": "rejected"})


    def set_2_draft(self):
        for obj in self:
            obj.write({"state": "draft"})

    def request(self):
        for obj in self:
            if obj.new_quantity < 0:
                raise ValidationError(_("Quantity cannot be negative."))
            obj.state = "requested"
            obj.auto_approve()

    def auto_approve(self):
        for obj in self:
            if obj.marketplace_seller_id.get_seller_global_fields('auto_approve_qty'):
                obj.with_user(SUPERUSER_ID)._approve()

    def change_product_qty(self):
        for template_obj in self:
            if not self.user_has_groups('stock.group_stock_manager'):
                raise UserError(_('Only inventory administrator has access to update the quantity.'))
            if template_obj.new_quantity < 0:
                raise ValidationError(_('Initial Quantity can not be negative'))
            vals = {
                'product_id': template_obj.product_id.id,
                'inventory_quantity' : template_obj.new_quantity,
                'location_id': template_obj.location_id.id,
            }
            self.env['stock.quant'].with_context(inventory_mode=True).create(vals).action_apply_inventory()

    def disable_seller_all_inventory_requests(self, seller_id):
        if seller_id:
            inventory_obj = self.search(
                [("marketplace_seller_id", "=", seller_id), ('state', '!=', 'approved')])
            inventory_obj.reject()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    marketplace_seller_id = fields.Many2one("res.partner", string="Seller")

    @api.model
    def _read_group_fill_results( self, domain, groupby, remaining_groupbys,
        aggregated_fields, count_field,read_group_result, read_group_order=None):

        if groupby == 'state':
            for result in read_group_result:
                state = result['state']
                if state in ["done", "cancel"]:
                    result['__fold'] = True
        return super(StockPicking, self)._read_group_fill_results(domain, groupby, remaining_groupbys,
            aggregated_fields, count_field, read_group_result, read_group_order)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(StockPicking, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        officer_group = self.env['ir.model.data'].check_object_reference(
            'odoo_marketplace', 'marketplace_officer_group')[1]
        groups_ids = self.env.user.sudo().groups_id.ids
        if officer_group not in groups_ids and result.get("toolbar", False):
            toolbar_dict = result.get("toolbar", {})
            toolbar_dict["action"] = []
            toolbar_dict["relate"] = []
            for key in toolbar_dict:
                # Remove options from Print menu for seller
                if key == "print":
                    print_list = toolbar_dict[key]
                    action_id = self.env.ref('stock.action_report_delivery').id
                    for print_list_item in print_list:
                        if print_list_item["id"] != action_id:
                            print_list.remove(print_list_item)
            result["toolbar"] = toolbar_dict
        return result

    # Replace the core method to resolved the ir.attachment modal create issue
    def _send_confirmation_email(self):
        for stock_pick in self.filtered(lambda p: p.company_id.stock_move_email_validation and p.picking_type_id.code == 'outgoing'):
            delivery_template_id = stock_pick.company_id.stock_mail_confirmation_template_id.id
            if stock_pick.marketplace_seller_id:
                stock_pick.sudo().with_context(force_send=True).message_post_with_template(delivery_template_id, email_layout_xmlid='mail.mail_notification_light')
            else:
                stock_pick.with_context(force_send=True).message_post_with_template(delivery_template_id, email_layout_xmlid='mail.mail_notification_light')

class StockMove(models.Model):
    _inherit = 'stock.move'

    marketplace_seller_id = fields.Many2one("res.partner", related="product_id.marketplace_seller_id", string="Seller", store=True)

    def _key_assign_picking(self):
        self.ensure_one()
        res = super(StockMove, self)._key_assign_picking()
        res = res + (self.product_id.marketplace_seller_id, )
        return res

    def _search_picking_for_assignation(self):
        self.ensure_one()
        picking = self.env['stock.picking'].search([
                ('group_id', '=', self.group_id.id),
                ('location_id', '=', self.location_id.id),
                ('location_dest_id', '=', self.location_dest_id.id),
                ('picking_type_id', '=', self.picking_type_id.id),
                ('marketplace_seller_id', '=', self.product_id.marketplace_seller_id.id),
                ('printed', '=', False),
                ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])], limit=1)
        return picking

    def _get_new_picking_values(self):
        values = super(StockMove, self)._get_new_picking_values()
        sellers = self.mapped('marketplace_seller_id')
        seller = len(sellers) == 1 and sellers.id or False
        values.update({
            "marketplace_seller_id" : seller
        })
        return values

    def shipped_mp_move(self):
        for rec in self:
            rec.sudo().action_done()
            sol_obj = self.env["sale.order.line"].sudo().search(
                [('order_id.name', '=', rec.origin), ('product_id', '=', rec.product_id.id)], limit=1)
            if sol_obj:
                sol_obj.marketplace_state = "shipped"

    def check_availability(self):
        for rec in self:
            rec.sudo().action_assign()

    def write(self, values):
        result = super(StockMove, self).write(values)
        for rec in self:
            if rec.state == "cancel":
                sol_obj = self.env["sale.order.line"].sudo().search([('order_id.name', '=', rec.origin), ('product_id', '=', rec.product_id.id)], limit=1)
                if sol_obj:
                    sol_obj.marketplace_state = "cancel"
            if rec.state == "done" and rec.sale_line_id:
                if rec.sale_line_id.qty_delivered == rec.sale_line_id.product_uom_qty:
                    rec.sale_line_id.marketplace_state = 'shipped'
                else:
                    rec.sale_line_id.marketplace_state = 'approved'
        return result
