# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

from odoo import _, api, fields, models
from odoo.osv import expression
from odoo.tools.translate import html_translate


class Website(models.Model):
    _inherit = 'website'

    dr_sale_special_offer = fields.Html(sanitize_attributes=False, translate=html_translate, sanitize_form=False)

    # PWA
    dr_pwa_activated = fields.Boolean()
    dr_pwa_name = fields.Char()
    dr_pwa_short_name = fields.Char()
    dr_pwa_background_color = fields.Char(default='#000000')
    dr_pwa_theme_color = fields.Char(default='#FFFFFF')
    dr_pwa_icon_192 = fields.Binary()
    dr_pwa_icon_512 = fields.Binary()
    dr_pwa_start_url = fields.Char(default='/shop')
    dr_pwa_offline_page = fields.Boolean()
    dr_pwa_version = fields.Integer(default=1)
    dr_pwa_shortcuts = fields.One2many('dr.pwa.shortcuts', 'website_id')

    def _get_brands(self, domain=[], limit=None, order=None):
        brand_attributes = self._get_brand_attributes().ids
        domain = expression.AND([domain, [('attribute_id', 'in', brand_attributes)]])
        return self.env['product.attribute.value'].search(domain, limit=limit, order=order)

    def _dr_has_b2b_access(self, record=None):
        if self._get_dr_theme_config('json_b2b_shop_config')['dr_enable_b2b']:
            return not self.env.user.has_group('base.group_public')
        return True

    def _get_brand_attributes(self):
        """ This will preserver the sequence """
        current_website_products = self.env['product.template'].search(self.sale_product_domain())
        all_brand_attributes = self.env['product.template']._get_brand_attribute()
        return self.env['product.template.attribute.line'].search([('product_tmpl_id', 'in', current_website_products.ids), ('attribute_id', 'in', all_brand_attributes.ids)]).mapped('attribute_id')

    def _get_dr_theme_config(self, key=False):
        """ See dr.theme.config for more info"""
        self.ensure_one()
        website_config = self.env['dr.theme.config']._get_all_config(self.id)
        website_config['is_public_user'] = not self.env.user.has_group('website.group_website_publisher')
        website_config['has_sign_up'] = False
        if website_config.get('json_b2b_shop_config')['dr_enable_b2b']:
            website_config['has_sign_up'] = self.env['res.users']._get_signup_invitation_scope() == 'b2c'
        if key:
            return website_config.get(key)
        return website_config

    def _get_pricelist_available(self, req, show_visible=False):
        if self._get_dr_theme_config('json_b2b_shop_config')['dr_only_assigned_pricelist'] and not self.env.user.has_group('base.group_website_designer'):
            return self.env.user.partner_id.property_product_pricelist
        return super()._get_pricelist_available(req, show_visible=show_visible)

    @api.model
    def get_theme_prime_shop_config(self):
        Website = self.get_current_website()
        return {'is_rating_active': Website.sudo().viewref('website_sale.product_comment').active, 'is_buy_now_active': Website.sudo().viewref('website_sale.product_buy_now').active, 'is_multiplier_active': Website.sudo().viewref('website_sale.product_quantity').active, 'is_wishlist_active': Website.sudo().viewref('website_sale_wishlist.add_to_wishlist').active, 'is_comparison_active': Website.sudo().viewref('website_sale_comparison.add_to_compare').active}

    def _get_website_category(self):
        return self.env['product.public.category'].search([('website_id', 'in', [False, self.id]), ('parent_id', '=', False)])

    def _get_theme_prime_rating_template(self, rating_avg, rating_count=False):
        return self.env["ir.ui.view"]._render_template('theme_prime.d_rating_widget_stars_static', values={
            'rating_avg': rating_avg,
            'rating_count': rating_count,
        })

    @api.model
    def get_theme_prime_bottom_bar_action_buttons(self):
        # Add to cart, blog, checkout, pricelist, language,
        return {'tp_home': {'name': _("Home"), 'url': '/', 'icon': 'fa fa-home'}, 'tp_search': {'name': _("Search"), 'icon': 'dri dri-search', 'action_class': 'tp-search-sidebar-action'}, 'tp_wishlist': {'name': _("Wishlist"), 'icon': 'dri dri-wishlist', 'url': '/shop/wishlist'}, 'tp_offer': {'name': _("Offers"), 'url': '/offers', 'icon': 'dri dri-bolt'}, 'tp_brands': {'name': _("Brands"), 'icon': 'dri dri-tag-l ', 'url': '/shop/all-brands'}, 'tp_category': {'name': _("Category"), 'icon': 'dri dri-category', 'action_class': 'tp-category-action'}, 'tp_orders': {'name': _("Orders"), 'icon': 'fa fa-file-text-o', 'url': '/my/orders'}, 'tp_cart': {'name': _("Cart"), 'icon': 'dri dri-cart', 'url': '/shop/cart'}, 'tp_lang_selector': {'name': _("Language and Pricelist selector")}}

    def _convert_currency_price(self, amount, from_base_currency=True, rounding_method=None):
        """ This function converts amount based website pricelist and company company currency

            :param amount: float or int,
            :param from_base_currency:  If True then coverts amount from company currency to pricelist currency
                                        else it converts pricelist currency to company currency
            :param rounding_method:  funcation reference to round the final amount
        """
        base_currency = self.company_id.currency_id
        pricelist_currency = self.get_current_pricelist().currency_id
        if base_currency != pricelist_currency:
            if from_base_currency:
                amount = base_currency._convert(amount, pricelist_currency, self.company_id, fields.Date.today())
            else:
                amount = pricelist_currency._convert(amount, base_currency, self.company_id, fields.Date.today())
        return rounding_method(amount) if rounding_method else amount

    # There is no versioning for all theme snippets (for the test case)
    def _is_snippet_used(self, snippet_module, snippet_id, asset_version, asset_type, html_fields):
        if snippet_module and snippet_module.startswith('theme_prime'):
            return True
        return super()._is_snippet_used(snippet_module, snippet_id, asset_version, asset_type, html_fields)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # PWA
    dr_pwa_activated = fields.Boolean(related='website_id.dr_pwa_activated', readonly=False)
    dr_pwa_name = fields.Char(related='website_id.dr_pwa_name', readonly=False)
    dr_pwa_short_name = fields.Char(related='website_id.dr_pwa_short_name', readonly=False)
    dr_pwa_background_color = fields.Char(related='website_id.dr_pwa_background_color', readonly=False)
    dr_pwa_theme_color = fields.Char(related='website_id.dr_pwa_theme_color', readonly=False)
    dr_pwa_icon_192 = fields.Binary(related='website_id.dr_pwa_icon_192', readonly=False)
    dr_pwa_icon_512 = fields.Binary(related='website_id.dr_pwa_icon_512', readonly=False)
    dr_pwa_start_url = fields.Char(related='website_id.dr_pwa_start_url', readonly=False)
    dr_pwa_shortcuts = fields.One2many(related='website_id.dr_pwa_shortcuts', readonly=False)
    dr_pwa_offline_page = fields.Boolean(related='website_id.dr_pwa_offline_page', readonly=False)

    def dr_open_pwa_shortcuts(self):
        self.website_id._force()
        action = self.env.ref('droggol_theme_common.dr_pwa_shortcuts_action').read()[0]
        action['domain'] = [('website_id', '=', self.website_id.id)]
        action['context'] = {'default_website_id': self.website_id.id}
        return action


class WebsiteSaleExtraField(models.Model):
    _inherit = 'website.sale.extra.field'

    dr_label = fields.Char(string="Display Label", translate=True)
    field_id = fields.Many2one(
        'ir.model.fields',
        domain=[('model_id.model', '=', 'product.template'), '|', ('ttype', 'in', ['char', 'binary']), ('name', 'in', ['public_categ_ids'])]
    )


# move to new file in v16
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        values = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        if self.website_id and not self.website_id._dr_has_b2b_access():
            for line in self.order_line:
                new_val = super(SaleOrder, self)._cart_update(product_id=line.product_id.id, line_id=line.id, add_qty=-1, set_qty=0, **kwargs)
                values.update(new_val)
        return values
