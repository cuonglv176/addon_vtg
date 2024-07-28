# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2019-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class WebsiteSiteMap(Website):
    @http.route(['/page/website.sitemap', '/page/sitemap'], type='http', auth="public", website=True)
    def website_sitemap(self, **post):
        domain=[
            ('parent_id','=',None),
            ('website_id','=',request.website.id),
        ]
        menu_ids = request.env['website.menu'].search(domain)
        values = {
            'menu_ids':menu_ids,
            'url_root': request.httprequest.url_root[:-1],
            'host':request.httprequest.host,
        }
        return request.render("website_seo_pro.sitemap",values)
