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

import werkzeug
import odoo
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db
from odoo import http
from odoo.http import request
# from odoo.addons.web.controllers.main import binary_content
import base64
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo import SUPERUSER_ID
from odoo.addons.website_sale.controllers.main import TableCompute, QueryURL, WebsiteSale
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.website_mail.controllers.main import WebsiteMail
from odoo.addons.website.controllers.main import Website
from odoo.addons.portal.controllers.web import Home
from odoo.addons.mail.controllers.mail import MailController
import logging
_logger = logging.getLogger(__name__)
import urllib.parse as urlparse
from urllib.parse import urlencode


PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

SPG = 20  # Shops/sellers Per Page
SPR = 4   # Shops/sellers Per Row


marketplace_domain = [('sale_ok', '=', True), ('state', '=', "approved")]

# class MailController(MailController):

#     @http.route()
#     def mail_init_messaging(self):
#         res = super(MailController, self).mail_init_messaging()
#         if request.env.user.check_user_is_draft_or_approved_seller():
#             partners_list = res.get("mention_partner_suggestions")
#             suggestions = []
#             for partners in partners_list:
#                 users = [p['user_id'] for p in partners if p.get('user_id')]
#                 users = request.env["res.users"].sudo().browse(users).exists()
#                 users = users.filtered(lambda u: u.check_user_is_mp_officer())
#                 partners = [p for p in partners if p.get('user_id') and p['user_id'] in users.ids]
#                 if partners:
#                     suggestions.append(partners)
#             res.update({
#                 "mention_partner_suggestions": suggestions,
#                 "public_partners": [],
#             })
#         return res

class Home(Home):

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        if request.session.uid:
            current_user = request.env['res.users'].sudo().browse(request.session.uid)
            if not current_user.has_group('base.group_user') and current_user.has_group('odoo_marketplace.marketplace_draft_seller_group') and current_user.partner_id.seller:
                request.uid = request.session.uid
                try:
                    context = request.env['ir.http'].webclient_rendering_context()
                    response = request.render('web.webclient_bootstrap', qcontext=context)
                    response.headers['X-Frame-Options'] = 'DENY'
                    return response
                except AccessError:
                    return werkzeug.utils.redirect('/web/login?error=access')
        return super(Home, self).web_client(s_action, **kw)

class AuthSignupHome(Website):

    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        ensure_db()
        response = super(AuthSignupHome, self).web_login(redirect=redirect, *args, **kw)
        if request.params['login_success']:
            current_user = request.env['res.users'].browse(request.uid)
            if not current_user.has_group('base.group_user') and current_user.has_group('odoo_marketplace.marketplace_draft_seller_group') and current_user.partner_id.seller:
                seller_dashboard_menu_id = request.env['ir.model.data'].check_object_reference('odoo_marketplace', 'wk_seller_dashboard')[1]
                redirect = "/web#menu_id=" + str(seller_dashboard_menu_id)
                return http.redirect_with_hash(redirect)
        return response

    def _signup_with_values(self, token, values):
        params = dict(request.params)
        is_seller = params.get('is_seller')
        country_id = params.get('country_id')
        if is_seller and is_seller == 'on':
            values.update({
                'is_seller' : True,
                'country_id' : int(country_id) if country_id else country_id,
                'url_handler' : params.get('url_handler'),
            })
        return super(AuthSignupHome, self)._signup_with_values(token, values)

    @http.route('/seller/signup', type='http', auth="public", website=True)
    def seller_signup_form(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()
        if kw.get("name", False):
            if 'error' not in qcontext and request.httprequest.method == 'POST':
                try:
                    self.do_signup(qcontext)
                    self.web_login(*args, **kw)
                    return website_marketplace_dashboard().account()
                except UserError as e:
                    qcontext['error'] = e.name or e.value
                except (SignupError, AssertionError) as e:
                    if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                        qcontext["error"] = _("Another user is already registered using this email address.")
                    else:
                        _logger.error("%s", e)
                        qcontext['error'] = _("Could not create a new account.")
            if kw.get("signup_from_seller_page", False) == "true":
                qcontext.pop("error")
                qcontext.update({"set_seller": True, 'hide_top_menu': True})

        return request.render('odoo_marketplace.mp_seller_signup', qcontext)


class website_marketplace_dashboard(http.Controller):

    @http.route(['/mp/terms/and/conditions'], type='json', auth="public", methods=['POST'], website=True)
    def mp_terms_and_conditions(self,**post):
        mp_t_and_c = post.get('mp_t_and_c',False)
        return request.env.ref("odoo_marketplace.mp_t_and_c_modal_template")._render({'mp_t_and_c':mp_t_and_c,},engine='ir.qweb')


    @http.route('/my/marketplace/become_seller', type='http', auth="public", website=True)
    def become_seller(self, **post):
        partner = request.env.user.partner_id
        if request.env.user.id == request.website.user_id.id:
            return request.redirect('/seller')
        if partner.user_id:
            sales_rep = partner.user_id
        else:
            sales_rep = False
        values = {
            'sales_rep': sales_rep,
            'company': request.website.company_id,
            'user': request.env.user,
            'countries': request.env['res.country'].sudo().search([]),
            'country' : partner.sudo().country_id if partner.sudo().country_id else partner.sudo().company_id.country_id,
        }
        return request.render('odoo_marketplace.convert_user_into_seller',values)

    @http.route('/my/marketplace/seller', type='http', auth="public", website=True)
    def submit_as_seller(self, **post):
        country_id = post.get('country_id',False)
        url_handler = post.get('url_handler',False)
        current_user = request.env.user

        if country_id and url_handler:
            current_user.partner_id.write({
                'country_id': int(country_id),
                'url_handler':url_handler,
                'seller': True,
            })
            draft_seller_group_id = request.env['ir.model.data'].check_object_reference('odoo_marketplace', 'marketplace_draft_seller_group')[1]
            groups_obj = request.env["res.groups"].browse(draft_seller_group_id)
            if groups_obj:
                for group_obj in groups_obj:
                    group_obj.sudo().write({"users": [(4, current_user.id, 0)]})

        return request.redirect('/my/marketplace/become_seller')

    @http.route('/my/marketplace', type='http', auth="public", website=True)
    def account(self):
        seller_dashboard_menu_id = request.env[
            'ir.model.data'].check_object_reference('odoo_marketplace', 'wk_seller_dashboard')[1]
        new_url = "/web#menu_id=" + str(seller_dashboard_menu_id)
        return request.redirect(new_url)


class MarketplaceSellerProfile(http.Controller):

    @http.route(['/profile/url/handler/vaidation'], type='json', auth="public", methods=['POST'], website=True)
    def profile_url_validation(self, url_handler, **post):
        model = post.get('model', False)
        url_handler = url_handler.lower()
        profile_or_shop_id = post.get('profile_or_shop_id',False)
        if model:
            if profile_or_shop_id:
                sameurl = request.env[model].sudo().search([('url_handler', '=', url_handler), ('id', '!=',int(profile_or_shop_id))])
            else:
                sameurl = request.env[model].sudo().search([('url_handler', '=', url_handler)])
        else:
            sameurl = request.env["res.partner"].sudo().search([('url_handler', '=', url_handler)])
        if len(sameurl) == 0:
            return True
        else:
            return False

    @http.route(['/seller/profile/<int:seller_id>',
        '/seller/profile/<int:seller_id>/page/<int:page>',
        '/seller/profile/<seller_url_handler>',
        '/seller/profile/<seller_url_handler>/page/<int:page>'],
        type='http', auth="public", website=True)
    def seller(self, seller_id=None, seller_url_handler=None, page=0, category=None, search='', ppg=False, **post):
        seller = url = False
        uid, context, env = request.uid, dict(request.env.context), request.env
        if seller_url_handler:
            seller = request.env["res.partner"].sudo().search([("url_handler", "=", str(seller_url_handler))], limit=1)
            url = "/seller/profile/" + str(seller.url_handler)
        elif seller_id:
            seller = env['res.partner'].sudo().browse(seller_id)
            wk_name = seller.sudo().name.strip().replace(" ", "-")
            url = '/seller/profile/' + wk_name + '-' + str(seller.id)
        if not seller or not seller.seller:
            return request.render("http_routing.403")
        
        if seller and not seller.website_published:
            officer_group = env.ref('odoo_marketplace.marketplace_officer_group')
            manager_group = env.ref('odoo_marketplace.marketplace_manager_group')
            user_obj = env.user
            group_bool_val = [i in user_obj.groups_id.ids for i in (officer_group.id,manager_group.id)]
            group_exist = True in group_bool_val
            if not group_exist and user_obj.url_handler != seller.url_handler:
                return request.render("http_routing.403")
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg

        PPR = request.env['website'].get_current_website().shop_ppr
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        if not context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = env['product.pricelist'].sudo().browse(context['pricelist'])

        # Calculate seller total sales count
        sales_count = 0
        all_products = request.env['product.template'].sudo().search(
            [("marketplace_seller_id", "=", seller.sudo().id)])
        for prod in all_products.with_user(SUPERUSER_ID):
            sales_count += prod.sales_count

        attrib_list = request.httprequest.args.getlist('attrib')
        url_for_keep = url
        keep = QueryURL(url_for_keep, category=category and int(
            category), search=search, attrib=attrib_list)

        seller_product_ids = request.env["product.template"].search([("marketplace_seller_id", "=", seller.id)])

        product_count = request.env["product.template"].sudo().search_count([('sale_ok', '=', True), ('status', '=', "approved"), ("website_published", "=", True), ("id", "in", seller_product_ids.ids)])
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = env['product.template'].sudo().search([('sale_ok', '=', True), ('status', '=', "approved"), ("website_published", "=", True), ("marketplace_seller_id", "=", seller.id)], limit=ppg, offset=pager['offset'], order='website_published desc, website_sequence desc')

        from_currency = env['res.users'].sudo().browse(uid).company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: env['res.currency'].sudo()._compute(from_currency, to_currency, price)

        recommend_id = request.env['seller.recommendation'].search([('seller_id', '=', seller.id), ('customer_id', '=', request.env.user.partner_id.id)], limit=1)

        values = {
            'seller': seller,
            'search': search,
            'rows': PPR,
            'bins': TableCompute().process(products, ppg, PPR),
            'ppg': ppg,
            'ppr': PPR,
            'pager': pager,
            'products': products,
            "keep": keep,
            'compute_currency': compute_currency,
            "pricelist": pricelist,
            "sales_count": sales_count,
            "already_recommend" : recommend_id.recommend_state if recommend_id else None,
            "product_count": int(product_count),
        }
        return request.render("odoo_marketplace.mp_seller_profile", values)

    @http.route('/seller/profile/recently-product/', type='json', auth="public", website=True)
    def seller_profile_recently_product(self, seller_id, page=0, category=None, search='', ppg=False, **post):
        if not seller_id:
            return False
        uid, context, env = request.uid, dict(request.env.context), request.env
        url = "/seller/" + str(seller_id)
        seller_obj = env["res.partner"].sudo().browse(seller_id)
        recently_product = request.website.mp_recently_product

        page = 0
        category = None
        search = ''
        ppg = False

        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg

        PPR = request.env['website'].get_current_website().shop_ppr
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        if not context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = env['product.pricelist'].sudo().browse(context['pricelist'])

        attrib_list = request.httprequest.args.getlist('attrib')
        keep = QueryURL('/profile/', category=category and int(category),
                        search=search, attrib=attrib_list)
        recently_product_obj = request.env['product.template'].search([
                ('sale_ok', '=', True),
                ('status', '=', "approved"),
                ("website_published", "=", True),
                ("marketplace_seller_id", "=", seller_obj.id)
            ],
            order='create_date desc, website_published desc, website_sequence desc',
            limit=recently_product
        )
        product_count = len(recently_product_obj.ids)
        pager = request.website.pager(
            url=url, total=product_count, page=page, step=20, scope=7, url_args=post)
        product_ids = request.env['product.template'].search([("id", "in", recently_product_obj.ids)], limit=ppg, offset=pager[
                                                             'offset'], order='website_published desc, website_sequence desc')
        products = env['product.template'].browse(product_ids.ids)
        from_currency = env['res.users'].sudo().browse(uid).company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: env['res.currency'].sudo()._compute(from_currency, to_currency, price)

        values = {
            'rows': PPR,
            'bins': TableCompute().process(products, ppg, PPR),
            'ppg': ppg,
            'ppr': PPR,
            'pager': pager,
            'products': products,
            "keep": keep,
            'compute_currency': compute_currency,
            "pricelist": pricelist,
            'seller_obj': seller_obj,
        }
        return request.env.ref('odoo_marketplace.shop_recently_product')._render(values, engine='ir.qweb')

    @http.route(['/marketplace/image/<int:partner_id>/<model_name>/<field_name>'], type='http', auth="public", website=True)
    def user_avatar(self, partner_id,model_name, field_name, **post):
        status, headers, content = request.env['ir.http'].binary_content(
            model=model_name, id=partner_id, field=field_name, default_mimetype='image/png', env=request.env(user=odoo.SUPERUSER_ID))

        if not content:
            img_path = odoo.modules.get_module_resource(
                'web', 'static/src/img', 'placeholder.png')
            with open(img_path, 'rb') as f:
                image = f.read()
            content = image.encode('base64')
        if status == 304:
            return werkzeug.wrappers.Response(status=304)
        image_base64 = base64.b64decode(content)
        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status = str(status)
        return response

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        return 'is_published desc,%s , id desc' % post.get('order', 'website_sequence desc')

    def _get_seller_search_domain(self, search):
        domain = [("website_published", "=", True), ("seller", '=', True), ("state", "=", "approved")]
        if search:
            for srch in search.split(" "):
                domain += [('name', 'ilike', srch)]
        return domain

    @http.route([
        '/sellers/list/',
        '/sellers/list/page/<int:page>',
    ], type='http', auth="public", website=True)
    def load_mp_all_seller(self, page=0, search='', ppg=False, **post):
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg

        PPR = request.env['website'].get_current_website().shop_ppr
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = SPG
            post["ppg"] = ppg
        else:
            ppg = SPG

        domain = self._get_seller_search_domain(search)
        keep = QueryURL('/sellers/list', search=search)

        url = "/sellers/list"
        if search:
            post["search"] = search

        seller_obj = request.env['res.partner']
        seller_count = seller_obj.sudo().search_count(domain)
        total_active_seller = seller_obj.sudo().search_count(self._get_seller_search_domain(""))
        pager = request.website.pager(url=url, total=seller_count, page=page, step=ppg, scope=7, url_args=post)
        seller_objs = seller_obj.sudo().search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

        values = {
            'search': search,
            'pager': pager,
            'seller_objs': seller_objs,
            'search_count': seller_count,  # common for all searchbox
            'bins': TableCompute().process(seller_objs, ppg, PPR),
            'ppg': ppg,
            'ppr': PPR,
            'rows': SPR,
            'keep': keep,
            'total_active_seller' : total_active_seller,
        }
        return request.render("odoo_marketplace.sellers_list", values)

    @http.route(['/seller/change_sequence'], type='json', auth="public")
    def change_sequence(self, id, sequence):
        seller_shop_obj = request.env['res.partner'].browse(id)
        if sequence == "top":
            seller_shop_obj.set_sequence_top()
        elif sequence == "bottom":
            seller_shop_obj.set_sequence_bottom()
        elif sequence == "up":
            seller_shop_obj.set_sequence_up()
        elif sequence == "down":
            seller_shop_obj.set_sequence_down()

    @http.route(['/seller/change_size'], type='json', auth="public")
    def change_size(self, id, x, y):
        seller_shop_obj = request.env['res.partner'].browse(id)
        return seller_shop_obj.write({'website_size_x': x, 'website_size_y': y})

    @http.route(['/seller/change_styles'], type='json', auth="public")
    def change_styles(self, id, style_id):
        seller_shop_obj = request.env['res.partner'].browse(id)

        remove = []
        active = False
        style_id = int(style_id)
        for style in seller_shop_obj.website_style_ids:
            if style.id == style_id:
                remove.append(style.id)
                active = True
                break

        style = request.env['seller.shop.style'].browse(style_id)

        if remove:
            seller_shop_obj.write({'website_style_ids': [(3, rid) for rid in remove]})
        if not active:
            seller_shop_obj.write({'website_style_ids': [(4, style.id)]})

class MarketplaceSellerShop(http.Controller):

    @http.route(['/seller/shop/<shop_url_handler>', '/seller/shop/<shop_url_handler>/page/<int:page>'], type='http', auth="public", website=True)
    def seller_shop(self, shop_url_handler, page=0, category=None, search='', ppg=False, **post):
        shop_obj = request.env["seller.shop"].sudo().search([("url_handler", "=", str(shop_url_handler))], limit=1)
        if not shop_obj:
            return False
        if not shop_obj.sudo().website_published and request.env.user.seller and request.env.user.url_handler != shop_obj.sudo().seller_id.url_handler:
            return request.render("http_routing.403")

        def _get_search_domain(search):
            domain = request.website.sale_product_domain()
            domain += [("marketplace_seller_id", "=",
                        shop_obj.sudo().seller_id.id)]

            if search:
                for srch in search.split(" "):
                    domain += [
                        '|', '|', '|', ('name', 'ilike',
                                        srch), ('description', 'ilike', srch),
                        ('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]
            product_obj = request.env['product.template'].sudo().search(domain)
            return request.env['product.template'].browse(product_obj.ids)

        uid, context, env = request.uid, dict(request.env.context), request.env
        url = "/seller/shop/" + str(shop_obj.url_handler)
        if search:
            post["search"] = search

        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg

        PPR = request.env['website'].get_current_website().shop_ppr
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        if not context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = env['product.pricelist'].sudo().browse(context['pricelist'])

        # Calculate seller total sales count
        sales_count = 0
        all_products = request.env['product.template'].sudo().search(
            [("marketplace_seller_id", "=", shop_obj.sudo().seller_id.id)])
        for prod in all_products.with_user(SUPERUSER_ID):
            sales_count += prod.sales_count

        attrib_list = request.httprequest.args.getlist('attrib')
        url_for_keep = '/seller/shop/' + str(shop_obj.url_handler)
        keep = QueryURL(url_for_keep, category=category and int(
            category), search=search, attrib=attrib_list)

        product_count = request.env["product.template"].sudo().search_count([('sale_ok', '=', True), ('status', '=', "approved"), ("website_published", "=", True), ("id", "in", shop_obj.sudo().seller_product_ids.ids)])
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        products = env['product.template'].sudo().search([('sale_ok', '=', True), ('status', '=', "approved"), ("website_published", "=", True), ("marketplace_seller_id", "=", shop_obj.sudo().seller_id.id)], limit=ppg, offset=pager['offset'], order='website_published desc, website_sequence desc')

        from_currency = env['res.users'].sudo().browse(uid).company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: env['res.currency'].sudo()._compute(from_currency, to_currency, price)
        shop_banner_url = request.website.image_url(shop_obj, 'shop_banner')

        values = {
            'shop_obj': shop_obj,
            'search': search,
            'rows': PPR,
            'bins': TableCompute().process(products if not search else _get_search_domain(search), ppg, PPR),
            'ppg': ppg,
            'ppr': PPR,
            'pager': pager,
            'products': products if not search else _get_search_domain(search),
            "keep": keep,
            'compute_currency': compute_currency,
            "pricelist": pricelist,
            'hide_pager': len(_get_search_domain(search)),
            'shop_banner_url': shop_banner_url,
            "sales_count": sales_count,
            "product_count": int(product_count),
        }

        return request.render("odoo_marketplace.mp_seller_shop", values)

    @http.route(['/seller/shop/change_sequence'], type='json', auth="public")
    def change_sequence(self, id, sequence):
        seller_shop_obj = request.env['seller.shop'].browse(id)
        if sequence == "top":
            seller_shop_obj.set_sequence_top()
        elif sequence == "bottom":
            seller_shop_obj.set_sequence_bottom()
        elif sequence == "up":
            seller_shop_obj.set_sequence_up()
        elif sequence == "down":
            seller_shop_obj.set_sequence_down()

    @http.route(['/seller/shop/change_size'], type='json', auth="public")
    def change_size(self, id, x, y):
        seller_shop_obj = request.env['seller.shop'].browse(id)
        return seller_shop_obj.write({'website_size_x': x, 'website_size_y': y})


    @http.route('/seller/shop/recently-product/', type='json', auth="public", website=True)
    def seller_shop_recently_product(self, shop_id, page=0, category=None, search='', ppg=False, **post):
        uid, context, env = request.uid, dict(request.env.context), request.env
        url = "/seller/shop/" + str(shop_id)
        shop_obj = env["seller.shop"].sudo().browse(shop_id)
        recently_product = request.website.mp_recently_product

        page = 0
        category = None
        search = ''
        ppg = False

        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg

        PPR = request.env['website'].get_current_website().shop_ppr
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        if not context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = env['product.pricelist'].sudo().browse(context['pricelist'])

        attrib_list = request.httprequest.args.getlist('attrib')
        keep = QueryURL('/shop', category=category and int(category),
                        search=search, attrib=attrib_list)

        recently_product_obj = request.env['product.template'].search([('sale_ok', '=', True), ('status', '=', "approved"), ("website_published", "=", True), (
            "marketplace_seller_id", "=", shop_obj.seller_id.id)], order='create_date desc, website_published desc, website_sequence desc', limit=recently_product)
        product_count = len(recently_product_obj.ids)
        pager = request.website.pager(
            url=url, total=product_count, page=page, step=20, scope=7, url_args=post)
        product_ids = request.env['product.template'].search([("id", "in", recently_product_obj.ids)], limit=ppg, offset=pager[
                                                             'offset'], order='website_published desc, website_sequence desc')
        products = env['product.template'].browse(product_ids.ids)

        from_currency = env['res.users'].sudo().browse(uid).company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: env['res.currency'].sudo()._compute(from_currency, to_currency, price)

        values = {
            'rows': PPR,
            'bins': TableCompute().process(products, ppg, PPR),
            'ppg': ppg,
            'ppr': PPR,
            'pager': pager,
            'products': products,
            "keep": keep,
            'compute_currency': compute_currency,
            "pricelist": pricelist,
            'shop_obj': shop_obj,
        }
        return request.env.ref('odoo_marketplace.shop_recently_product')._render(values, engine='ir.qweb')

    @http.route(['/seller', '/seller/login'], type='http', auth="public", website=True)
    def mp_sell(self, redirect=None, **post):
        uid, context, env = request.uid, dict(request.env.context), request.env
        ensure_db()
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        values.update({
            "hide_top_menu": True,
            "test": True,
            "signup_enabled": request.env['res.users']._get_signup_invitation_scope() == 'b2c',
        })
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = request.session.authenticate(request.session.db, request.params[
                                               'login'], request.params['password'])
            if uid is not False:
                request.params['login_success'] = True
                if not redirect:
                    redirect = '/web'
                return http.redirect_with_hash(redirect)
            request.uid = old_uid
            values['error'] = "Wrong login/password"
        return request.render("odoo_marketplace.wk_mp_seller_landing_page", values)


    @http.route(['/add/header/button'], type='json', auth="public", website=True)
    def add_header_button(self, **post):
        route = ''
        if request.env.user._is_admin() or request.env.user == request.website.user_id:
            route = '/seller/signup'
        elif request.env.user.is_marketplace_user():
            route = '/my/marketplace'
        else:
            route = '/my/marketplace/become_seller'
        return route

    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        return 'is_published desc,%s , id desc' % post.get('order', 'website_sequence desc')

    def _get_seller_shop_search_domain(self, search):
            domain = [("website_published", "=", True)]

            if search:
                for srch in search.split(" "):
                    domain += [
                        '|', ('name', 'ilike',
                                        srch), ('description', 'ilike', srch)]
            return domain


    @http.route([
        '/seller/shops/list/',
        '/seller/shops/list/page/<int:page>',
    ], type='http', auth="public", website=True)
    def load_mp_all_seller_shop(self, page=0, search='', ppg=False, **post):
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        PPR = request.env['website'].get_current_website().shop_ppr or 4

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = SPG
            post["ppg"] = ppg
        else:
            ppg = SPG

        domain = self._get_seller_shop_search_domain(search)
        keep = QueryURL('/seller/shops/list', search=search)

        url = "/seller/shops/list"
        if search:
            post["search"] = search

        seller_shop_obj = request.env['seller.shop']
        seller_shop_count = seller_shop_obj.sudo().search_count(domain)
        pager = request.website.pager(url=url, total=seller_shop_count, page=page, step=ppg, scope=7, url_args=post)
        seller_shops = seller_shop_obj.sudo().search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

        values = {
            'search': search,
            'pager': pager,
            'seller_shops': seller_shops,
            'search_count': seller_shop_count,  # common for all searchbox
            'bins': TableCompute().process(seller_shops, ppg, PPR),
            'ppg': ppg,
            'ppr': PPR,
            'rows': SPR,
            'keep': keep,
        }
        return request.render("odoo_marketplace.seller_shop_list", values)

class SellerReview(http.Controller):

    @http.route(['/seller/review'], type='json', auth="public", website=True)
    def review(self, **post):
        if post.get('review') and post.get('title') and post.get('stars'):
            review_dict = {}
            review_dict['msg'] = post.get('review')
            review_dict['rating'] = int(post.get('stars'))
            review_dict['title'] = post.get('title')
            review_dict['marketplace_seller_id'] = post.get('seller_id')
            review_dict["partner_id"] = request.env.user.partner_id.id
            review_dict["website_published"] = request.website.mp_review_auto_publish
            review_obj = request.env['seller.review'].sudo().create(review_dict)
            message_to_publish = request.website.mp_message_to_publish
            if message_to_publish:
                return message_to_publish
            else:
                return "  Congratulation!!! your review has been submitted successfully."
        return "  Congratulation!!! your review has been submitted successfully."

    @http.route(['/seller/shop/change_styles'], type='json', auth="public")
    def change_styles(self, id, style_id):
        seller_shop_obj = request.env['seller.shop'].browse(id)

        remove = []
        active = False
        style_id = int(style_id)
        for style in seller_shop_obj.website_style_ids:
            if style.id == style_id:
                remove.append(style.id)
                active = True
                break

        style = request.env['seller.shop.style'].browse(style_id)

        if remove:
            seller_shop_obj.write({'website_style_ids': [(3, rid) for rid in remove]})
        if not active:
            seller_shop_obj.write({'website_style_ids': [(4, style.id)]})


    @http.route(['/seller/review/help'], type='json', auth="public", methods=['POST'], website=True)
    def review_help(self,  seller_review_id, review_help=0,  **post):
        review_help_obj = request.env['review.help']
        res = []
        if not seller_review_id:
            return False
        if review_help == 0:
            return False
        if seller_review_id and review_help:
            review_help_ids = request.env['review.help'].search(
                [('seller_review_id', '=', seller_review_id), ('customer_id', '=', request.env.user.partner_id.id)])
            if review_help_ids:
                review_help_id = review_help_obj.browse(review_help_ids[0])
                if review_help == 1:
                    review_help_ids[0].write({"review_help": "yes"})
                if review_help == -1:
                    review_help_ids[0].write({"review_help": "no"})
                if review_help == 2:
                    review_help_ids[0].write({"review_help": "no"})
                if review_help == -2:
                    review_help_ids[0].write({"review_help": "yes"})
            else:
                if review_help == 1:
                    review_help_obj.sudo().create(
                        {"customer_id": request.env.user.partner_id.id, "seller_review_id": seller_review_id, "review_help": "yes"})
                if review_help == -1:
                    review_help_obj.sudo().create(
                        {"customer_id": request.env.user.partner_id.id, "seller_review_id": seller_review_id, "review_help": "no"})
            review_obj = request.env['seller.review'].browse(seller_review_id)
            review_obj.sudo()._set_total_helpful()  # Call depends method manually
            review_obj.sudo()._set_total_not_helpful()  # Call depends method manually
            res.append(review_obj.helpful)
            res.append(review_obj.not_helpful)
        return res

    @http.route(['/seller/load/review'], type='json', auth="public", website=True)
    def load_seller_review(self, seller_id, offset=0, limit=False, sort_by="recent", filter_by=-1, **kwargs):
        seller_obj = request.env['res.partner']
        return_review_obj = seller_obj.sudo().fetch_active_review2(
            seller_id, int(offset), limit, sort_by, filter_by)
        values = {
            'seller_review_ids': return_review_obj,
            'seller': request.env['res.partner'].sudo().browse(seller_id),
        }
        return request.env.ref("odoo_marketplace.wk_seller_review_template")._render(values, engine='ir.qweb')

    @http.route(['/seller/load/review/count'], type='json', auth="public", website=True)
    def load_seller_review_count(self, seller_id, offset=0, limit=False, sort_by="recent", filter_by=-1, **kwargs):
        seller_obj = request.env['res.partner']
        return_seller_review_obj = seller_obj.sudo().fetch_active_review2(
            seller_id, int(offset), limit, sort_by, filter_by)
        if filter_by == -1:
            review_ids = request.env["seller.review"].search([('marketplace_seller_id', '=', seller_id), (
                'website_published', '=', True)], order="helpful desc" if sort_by == "most_helpful" else "create_date desc")
        if filter_by == 1:
            review_ids = request.env["seller.review"].search([('marketplace_seller_id', '=', seller_id), ('website_published', '=', True), (
                'rating', '=', 1)], order="helpful desc" if sort_by == "most_helpful" else "create_date desc")
        if filter_by == 2:
            review_ids = request.env["seller.review"].search([('marketplace_seller_id', '=', seller_id), ('website_published', '=', True), (
                'rating', '=', 2)], order="helpful desc" if sort_by == "most_helpful" else "create_date desc")
        if filter_by == 3:
            review_ids = request.env["seller.review"].search([('marketplace_seller_id', '=', seller_id), ('website_published', '=', True), (
                'rating', '=', 3)], order="helpful desc" if sort_by == "most_helpful" else "create_date desc")
        if filter_by == 4:
            review_ids = request.env["seller.review"].search([('marketplace_seller_id', '=', seller_id), ('website_published', '=', True), (
                'rating', '=', 4)], order="helpful desc" if sort_by == "most_helpful" else "create_date desc")
        if filter_by == 5:
            review_ids = request.env["seller.review"].search([('marketplace_seller_id', '=', seller_id), ('website_published', '=', True), (
                'rating', '=', 5)], order="helpful desc" if sort_by == "most_helpful" else "create_date desc")
        return [len(return_seller_review_obj), len(review_ids)]

    @http.route(['/seller/recommend'], type='json', auth="public", website=True)
    def seller_recommend(self, seller_id, recommend_state="no", **kwargs):
        recommend_obj = request.env['seller.recommendation']
        if not seller_id:
            return False

        recommend_ids = recommend_obj.search(
            [('seller_id', '=', seller_id), ('customer_id', '=', request.env.user.partner_id.id)])
        if recommend_ids:
            for rec in recommend_ids:
                rec.sudo().write({"recommend_state": recommend_state})
        else:
            recommend_obj.sudo().create({"customer_id": request.env.user.partner_id.id,
                                         "seller_id": seller_id, "recommend_state": recommend_state})
        return True

    @http.route(['/seller/review/check'], type='json', auth="public", website=True)
    def check_seller_review(self, seller_id, **kwargs):
        return_message = ""
        sol_objs = request.env["sale.order.line"].sudo().search(
            [("product_id.marketplace_seller_id", "=", seller_id), ("order_id.partner_id", "=", request.env.user.partner_id.id), ("order_id.state", "in", ["sale", "done"])])
        for_seller_total_review_obj = request.env["seller.review"].sudo().search(
            [('marketplace_seller_id', '=', seller_id), ('partner_id', '=', request.env.user.partner_id.id)])

        # This code must be used in create of review
        if len(sol_objs.ids) == 0:
            return_message = _(
                "You have to purchase a product of this seller first.")
            return return_message
        elif len(for_seller_total_review_obj.ids) >= len(sol_objs.ids):
            return_message = _(
                "According to your purchase your review limit is over.")
            return return_message
        else:
            return True

class TrackSol(http.Controller):
    @http.route('/track/sol', type='json', auth="public", website=True)
    def track_order_line(self, sol_id, **kwargs):
        if not sol_id:
            return False
        values = {
            'sol_id': request.env["sale.order.line"].sudo().browse(sol_id),
        }
        return request.env.ref("odoo_marketplace.marketplace_order_line_info")._render(values, engine='ir.qweb')

class MarketplaceMail(http.Controller):
    @http.route(['/marketplace_mail/post/json'], type='json', auth='public', website=True)
    def mp_chatter_json(self, res_model='', res_id=None, message='', **kw):
        res_id = int(res_id) if res_id else res_id
        data = WebsiteMail().chatter_json(res_model, res_id, message, **kw)
        if data:
            return request.env.ref("odoo_marketplace.mp_chatter_mail_append")._render(data, engine='ir.qweb')
        else:
            return False

class WebsiteSale(WebsiteSale):

    @http.route('/shop/products/autocomplete', type='json', auth='public', website=True)
    def products_autocomplete(self, term, options={}, **kwargs):
        res = super(WebsiteSale, self).products_autocomplete(term=term, options=options, kwargs=kwargs)
        url = request.httprequest.referrer
        url_parts = list(urlparse.urlparse(url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        if url_parts and url_parts[2] and '/seller/shop/' in url_parts[2]:
            url_handler = url_parts[2].split("/seller/shop/",1)[1]
            shop = request.env['seller.shop'].sudo().search([('url_handler','=',url_handler)], limit=1)
            seller_id = shop.seller_id and shop.seller_id.id
            if seller_id and res.get('products'):
                ProductTemplate = request.env['product.template']
                prod_list = []
                for product in range(len(res.get('products'))):
                    product_tmpl_id = res.get('products')[product]
                    prod_obj = ProductTemplate.browse(product_tmpl_id.get('product_template_id'))
                    if prod_obj and prod_obj.marketplace_seller_id and prod_obj.marketplace_seller_id.id == seller_id:
                        prod_list.append(res.get('products')[product])
                res.update({'products' : prod_list, 'products_count': len(prod_list)})
        return res
