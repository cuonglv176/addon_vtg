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
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Default methods
    def _get_default_category_id(self):
        if self.marketplace_seller_id:
            mp_categ = self.env['res.config.settings'].get_mp_global_field_value('internal_categ')
            if mp_categ:
                return mp_categ.id
        elif self._context.get("pass_default_categ"):
            return False
        return super(ProductTemplate, self)._get_default_category_id()

    # Fields declaration

    categ_id = fields.Many2one(
        'product.category', 'Internal Category',
        change_default=True, default=_get_default_category_id,
        required=True, help="Select category for the current product")
    status = fields.Selection([('draft', 'Draft'), ('pending', 'Pending'), (
        'approved', 'Approved'), ('rejected', 'Rejected')], "Marketplace Status", default="draft", copy=False, tracking=True)
    mp_qty = fields.Float(string="Initial Quantity",
                       help="Initial quantity of the product which you want to update in warehouse for inventory purpose.", copy=False)
    template_id = fields.Many2one(
        "product.template", string="Product Template Id", copy=False)
    marketplace_seller_id = fields.Many2one(
        "res.partner", string="Seller", default=lambda self: self.env.user.partner_id.id if self.env.user.partner_id and self.env.user.partner_id.seller else self.env['res.partner'], copy=False, tracking=True, help="If product has seller then it will consider as marketplace product else it will consider as simple product.")
    color = fields.Integer('Color Index')
    pending_qty_request = fields.Boolean(
        string="Request Pending", compute="_get_pending_qty_request")
    is_initinal_qty_set = fields.Boolean("Initial Qty Set")
    activity_date_deadline = fields.Date(
        'Next Activity Deadline', related='activity_ids.date_deadline',
        readonly=True, store=True,
        groups="base.group_user,odoo_marketplace.marketplace_seller_group")
    item_ids = fields.One2many('product.pricelist.item', 'product_tmpl_id', 'Pricelist Items')

    @api.model
    def _read_group_fill_results( self, domain, groupby, remaining_groupbys,
        aggregated_fields, count_field,read_group_result, read_group_order=None):

        if groupby == 'status':
            for result in read_group_result:
                state = result['status']
                if state in ['rejected','draft']:
                    result['__fold'] = True
        return super(ProductTemplate, self)._read_group_fill_results(domain, groupby, remaining_groupbys,
            aggregated_fields, count_field, read_group_result, read_group_order)

    # SQL Constraints

    # compute and search field methods, in the same order of fields declaration

    @api.model
    def _get_pending_qty_request(self):
        for obj in self:
            mp_stock_obj = self.env["marketplace.stock"].search(
                [('product_temp_id', '=', obj.id), ('state', '=', 'requested')])
            obj.pending_qty_request = True if mp_stock_obj else False

    # Constraints and onchanges

    @api.onchange("marketplace_seller_id")
    def onchange_seller_id(self):
        self.status = "draft" if self.marketplace_seller_id and not self.status else False
        self.categ_id = self.env['res.config.settings'].get_mp_global_field_value('internal_categ')

    # CRUD methods (and name_get, name_search, ...) overrides

    @api.model
    def create(self, vals):
        ''' Set default false to sale_ok and purchase_ok for seller product'''
        partner = self.env["res.partner"].sudo().browse(vals.get("marketplace_seller_id", False)) or self.env.user.partner_id
        if partner and partner.sudo().seller:
            if not vals.get("sale_ok", False):
                vals["sale_ok"] = False
            if not vals.get("purchase_ok", False):
                vals["purchase_ok"] = False
            if not vals.get("status", False):
                vals["status"] = "draft"
            if vals.get('type', False) and vals['type'] != 'service' and not vals.get("invoice_policy", False):
                vals["invoice_policy"] = "delivery"
            mp_categ = self.env['res.config.settings'].get_mp_global_field_value('internal_categ')
            if mp_categ:
                vals["categ_id"] = mp_categ
        product_template = super(ProductTemplate, self).create(vals)
        return product_template

    # Action methods

    def toggle_website_published(self):
        """ Inverse the value of the field ``website_published`` on the records in ``self``. """
        for record in self:
            if record.marketplace_seller_id and record.status != 'approved' and not record.website_published:
                raise UserError(_("You cannot publish unapproved products."))
            record.website_published = not record.website_published

    def mp_action_view_sales(self):
        self.ensure_one()
        action = self.env.ref('odoo_marketplace.wk_seller_slae_order_line_action')
        product_ids = self.product_variant_ids.ids
        tree_view_id = self.env.ref('odoo_marketplace.wk_seller_product_order_line_tree_view')
        form_view_id = self.env.ref('odoo_marketplace.wk_seller_product_order_line_form_view')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'binding_view_types': action.binding_view_types,
            'view_mode': action.view_mode,
            'views': [(tree_view_id.id, 'tree'), (form_view_id.id, 'form')],
            'target': action.target,
            'context': "{'default_product_id': " + str(product_ids[0]) + "}",
            'res_model': action.res_model,
            'domain': [('state', 'in', ['sale', 'done']), ('product_id.product_tmpl_id', '=', self.id)],
        }

    def pending_qty_stock_request(self):
        for rec in self:
            pending_stock = self.env["marketplace.stock"].search([('product_temp_id','=',rec.id),('state','=','requested')])
            return {
                'name':'Update Marketplace Product Quantity',
                'type':'ir.actions.act_window',
                'res_model':'marketplace.stock',
                'view_mode':'form',
                'binding_view_types':'form',
                'res_id' : pending_stock[0].id,
                'target':'current',
            }

    # Business methods

    def send_mail_to_seller(self, mail_templ_id):
        """ """
        if not mail_templ_id:
            return False
        template_obj = self.env['mail.template'].browse(mail_templ_id)
        template_obj.with_company(self.env.company).send_mail(self.id, True)

    def auto_approve(self):
        for obj in self:
            auto_product_approve = obj.marketplace_seller_id.get_seller_global_fields('auto_product_approve')
            if auto_product_approve:
                obj.write({"status": "pending"})
                obj.sudo().approved()
            else:
                obj.write({"status": "pending"})
        return True

    def check_state_send_mail(self):
        resConfig = self.env['res.config.settings']
        for obj in self.filtered(lambda o: o.status in ["approved", "rejected"]):
            # Notify to admin by admin when product approved/reject
            if resConfig.get_mp_global_field_value("enable_notify_admin_on_product_approve_reject"):
                temp_id = resConfig.get_mp_global_field_value("notify_admin_on_product_approve_reject_m_tmpl_id")
                if temp_id:
                    self.send_mail_to_seller(temp_id)
            # Notify to Seller by admin  when product approved/reject
            if resConfig.get_mp_global_field_value("enable_notify_seller_on_product_approve_reject"):
                temp_id = resConfig.get_mp_global_field_value("notify_seller_on_product_approve_reject_m_tmpl_id")
                if temp_id:
                    self.send_mail_to_seller(temp_id)

    def approved(self):
        for obj in self:
            if not obj.marketplace_seller_id:
                raise Warning(_("Marketplace seller id is not assign to this product."))
            if obj.marketplace_seller_id.state == "approved":
                if obj.product_variant_ids:
                    if obj.marketplace_seller_id.get_seller_global_fields('auto_product_approve'):
                        obj.product_variant_ids.set_to_approved()
                        obj.sudo().write({"status": "approved", "sale_ok": True})
                        obj.check_state_send_mail()
                        if not obj.is_initinal_qty_set and len(obj.product_variant_ids) == 1:
                            obj.set_initial_qty()
                    else:
                        form_view_ref = self.env.ref('odoo_marketplace.wk_product_variant_wizard_view')
                        return {
                            'name':'Product Approval Wizard' ,
                            'type': 'ir.actions.act_window',
                            'binding_view_types': 'form',
                            'view_id': form_view_ref.id,
                            'view_mode': 'form',
                            'res_model': 'variant.approval.wizard',
                            'nodestroy': True,
                            'target': 'new',
                        }
                else:
                    obj.sudo().write({"status": "approved", "sale_ok": True})
                    obj.check_state_send_mail()
                    if not obj.is_initinal_qty_set and len(obj.product_variant_ids) == 1:
                        obj.set_initial_qty()
            else:
                raise Warning(
                    _("Marketplace seller of this product is not approved."))
        return True

    def reject(self):
        for product_obj in self:
            if product_obj.status in ("draft", "pending", "approved") and product_obj.marketplace_seller_id:
                product_obj.write({
                    "sale_ok": False,
                    "website_published": False,
                    "status": "rejected"
                })
                ###########Variant Rejected###########
                for variant in product_obj.product_variant_ids:
                    variant.set_to_rejected()
                product_obj.check_state_send_mail()

    # Called in server action
    def approve_product(self):
        self.filtered(lambda o: o.status == "pending" and o.marketplace_seller_id).approved()

    # Called in server action
    def reject_product(self):
        self.filtered(lambda o: o.status in ("draft", "pending", "approved") and o.marketplace_seller_id).reject()

    def set_initial_qty(self):
        for template_obj in self:
            location_id = template_obj.marketplace_seller_id.get_seller_global_fields('location_id')
            if len(self) == 1:
                if template_obj.mp_qty < 0:
                    raise Warning(_('Initial Quantity can not be negative'))
            if not location_id:
                raise Warning(_("Product seller has no location/warehouse."))
            if template_obj.mp_qty > 0:
                vals = {
                    'product_id': template_obj.product_variant_ids[0].id,
                    'product_temp_id': template_obj.id,
                    'new_quantity': template_obj.mp_qty,
                    'location_id': location_id or False,  # Phase 2
                    'note': _("Initial Quantity."),
                    'state': "requested",
                }
                mp_product_stock = self.env['marketplace.stock'].create(vals)
                template_obj.is_initinal_qty_set = True
                mp_product_stock.auto_approve()

    def disable_seller_all_products(self, seller_id):
        if seller_id:
            product_objs = self.search(
                [("marketplace_seller_id", "=", seller_id), ("status", "not in", ["draft", "rejected"])])
            product_objs.reject()

    def set_pending(self):
        for rec in self:
            ###########Variant Pending###########
            if rec.product_variant_ids:
                rec.product_variant_ids.set_to_pending()
            rec.auto_approve()

    def send_to_draft(self):
        for rec in self:
            ###########Variant Draft###########
            for variant in rec.product_variant_ids:
                variant.set_to_draft()
            rec.write({"status": "draft"})

    def write(self, vals):
        if vals.get("marketplace_seller_id", False):
            for rec in self:
                if rec.marketplace_seller_id and rec.status not in ["draft", "pending"]:
                    raise UserError(_('You cannot change the seller of the product that already contains seller.'))
        return super(ProductTemplate, self).write(vals)

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, pricelist=False, parent_combination=False, only_template=False):
        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty, pricelist=pricelist,
            parent_combination=parent_combination, only_template=only_template)

        if not self.env.context.get('website_sale_stock_get_quantity'):
            return combination_info

        if combination_info['product_id']:
            product = self.env['product.product'].sudo().browse(combination_info['product_id'])
            seller_obj = product.marketplace_seller_id
            if seller_obj and seller_obj.seller:
                warehouse_id = seller_obj.get_seller_global_fields("warehouse_id")
                if warehouse_id:
                    product.with_context(warehouse=warehouse_id)._compute_quantities()
                    combination_info.update({
                        'virtual_available': product.virtual_available,
                    })
        return combination_info

    def _get_own_attribute_exclusions(self):
        self.ensure_one()
        vals = super()._get_own_attribute_exclusions()
        attribute_objs_list = [variant.product_template_attribute_value_ids for variant in self.product_variant_ids if variant.marketplace_status != 'approved']
        for attribute_ids in attribute_objs_list:
            if attribute_ids:
                ret_val = vals.get(attribute_ids[0].id,[])
                index = 1 if len(attribute_ids)>1 else 0
                ret_val.extend(attribute_ids[index:].ids)
                vals[attribute_ids[0].id] = list(set(ret_val))
        return vals

class ProductProduct(models.Model):
    _inherit = 'product.product'

    activity_date_deadline = fields.Date(
        'Next Activity Deadline', related='activity_ids.date_deadline',
        readonly=True, store=True,
        groups="base.group_user,odoo_marketplace.marketplace_seller_group")
    mp_var_qty = fields.Float(string="Initial Variant Quantity",
                       help="Initial quantity of the product which you want to update in warehouse for inventory purpose.", copy=False)
    is_var_initinal_qty_set = fields.Boolean("Initial Variant Qty Set")
    marketplace_status = fields.Selection([('draft', 'Draft'), ('pending', 'Pending'), (
        'approved', 'Approved'), ('rejected', 'Rejected')], "Marketplace Variant Status", default="draft", copy=False)

    # Action methods

    def set_var_initial_qty(self):
        for var_obj in self:
            if var_obj.mp_var_qty < 0:
                raise Warning(_('Initial Quantity can not be negative'))
            if not var_obj.marketplace_seller_id.location_id:
                raise Warning(_("Product seller has no location/warehouse."))
            if var_obj.mp_var_qty > 0:
                vals = {
                    'product_id': var_obj.id,
                    'product_temp_id': var_obj.product_tmpl_id.id,
                    'new_quantity': var_obj.mp_var_qty,
                    'location_id': var_obj.marketplace_seller_id.location_id.id or False,  # Phase 2
                    'note': _("Initial Quantity."),
                    'state': "requested",
                }
                mp_product_stock = self.env['marketplace.stock'].create(vals)
                var_obj.is_var_initinal_qty_set = True
                mp_product_stock.auto_approve()

    def set_to_approved(self):
        for obj in self:
            if not obj.is_var_initinal_qty_set and len(obj.product_variant_ids) > 1:
                obj.set_var_initial_qty()
            obj.marketplace_status = "approved"
        return True

    def set_to_pending(self):
        for obj in self:
            if obj.marketplace_seller_id.auto_product_approve:
                obj.marketplace_status = "approved"
            else:
                obj.marketplace_status = "pending"
        return True

    def set_to_draft(self):
        for obj in self:
            obj.marketplace_status = "draft"
        return True

    def set_to_rejected(self):
        for obj in self:
            obj.marketplace_status = "rejected"
        return True

    @api.model
    def create(self, vals):
        product_variant = super(ProductProduct, self).create(vals)
        if product_variant.product_tmpl_id.marketplace_seller_id:
            if product_variant.product_tmpl_id.status != 'approved':
                product_variant.sudo().write({'marketplace_status':product_variant.product_tmpl_id.status})
            else:
                if product_variant.product_tmpl_id.marketplace_seller_id.auto_product_approve:
                    product_variant.sudo().write({'marketplace_status':'approved'})
                else:
                    product_variant.sudo().write({'marketplace_status':'pending'})
        return product_variant

    def toggle_website_published(self):
        """ Inverse the value of the field ``website_published`` on the records in ``self``. """
        for record in self:
            record.product_tmpl_id.toggle_website_published()

    def mp_action_view_sales(self):
        self.ensure_one()
        action = self.env.ref('odoo_marketplace.wk_seller_slae_order_line_action')
        tree_view_id = self.env.ref('odoo_marketplace.wk_seller_product_order_line_tree_view')
        form_view_id = self.env.ref('odoo_marketplace.wk_seller_product_order_line_form_view')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'binding_view_types': action.binding_view_types,
            'view_mode': action.view_mode,
            'views': [(tree_view_id.id, 'tree'), (form_view_id.id, 'form')],
            'target': action.target,
            'context': "{'default_product_id': " + str(self.id) + "}",
            'res_model': action.res_model,
            'domain': [('state', 'in', ['sale', 'done']), ('product_id', '=', self.id)],
        }

    def pending_qty_stock_request(self):
        for rec in self:
            pending_stock = self.env["marketplace.stock"].search([('product_id','=',rec.id),('state','=','requested')])
            return {
                'name':'Update Marketplace Product Quantity',
                'type':'ir.actions.act_window',
                'res_model':'marketplace.stock',
                'view_mode':'form',
                'binding_view_types':'form',
                'res_id' : pending_stock[0].id,
                'target':'current',
            }
