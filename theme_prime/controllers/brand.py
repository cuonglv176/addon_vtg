# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

import string
from collections import defaultdict

from odoo import http
from odoo.http import request
from odoo.osv import expression


class ThemePrimeBrand(http.Controller):

    @http.route('/shop/all-brands', type='http', auth='public', website=True, sitemap=True)
    def brands(self, search='', **args):
        is_disable_grouping = request.website._get_dr_theme_config('json_brands_page')['disable_brands_grouping']
        if search:
            brands = request.website._get_brands([('name', 'ilike', search)])
        else:
            brands = request.website._get_brands([])

        grouped_brands = defaultdict(list)
        if is_disable_grouping:
            grouped_brands = {'All Brands': brands}
        else:
            alphabet_range = string.ascii_uppercase
            grouped_brands.update((alphabet, []) for alphabet in alphabet_range)
            for brand in brands:
                first_char = str.upper(brand.name[:1])
                grouped_brands[first_char].append(brand)

        get_brand_count = request.env['product.template']._get_product_attrib_count(attrib_values=[[brand.attribute_id.id, brand.id] for brand in brands], domain=request.env['website'].sale_product_domain())

        return request.render('theme_prime.all_brands', {'is_disable_grouping': is_disable_grouping, 'grouped_brands': grouped_brands, 'search': search, 'get_brand_count': get_brand_count})
