# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

import re
from odoo import fields, models, api


class DrWebsiteCategoryLabel(models.Model):
    _name = 'dr.product.public.category.label'
    _description = 'Category Label'

    name = fields.Char(required=True, translate=True)
    background_color = fields.Char('Background Color', default='#000000')
    text_color = fields.Char('Text Color', default='#FFFFFF')


class DrProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    dr_category_label_id = fields.Many2one('dr.product.public.category.label', string='Label')
    dr_category_cover_image = fields.Binary(string='Cover Image')
    dr_category_icon = fields.Binary(string='Icon Image')
    dr_search_formulate = fields.Boolean(string='Formulated Search', help="Use to search multi level categories \
        e.g. Men Shirt (Here men and shirt are diffrent category but will be displayed as one in smart search)")
    ds_name = fields.Char(string='Search DS Name', compute="_compute_ds_name", search="_search_ds_name")

    def _compute_ds_name(self):
        for category in self:
            if self.env.context.get('dr_formulate'):
                category.ds_name = " ".join([categ.name for categ in category.parents_and_self if (category.id == categ.id or categ.dr_search_formulate)])
            else:
                category.ds_name = category.name

    @api.model
    def _search_ds_name(self, operator, value):
        if not self.env.context.get('dr_formulate'):
            return [('name', operator, value)]

        # Assumes operator is 'ilike'
        domain, website_id = [('dr_search_formulate', '=', False)], self.env.context.get('website_id')
        if website_id:
            domain += self.env['website'].website_domain(website_id=website_id)
        categ_ids = [categ.id for categ in self.search(domain) if re.search(re.escape(value), categ.ds_name, re.IGNORECASE)]
        return [('id', 'in', categ_ids)]

    @api.model
    def _search_get_detail(self, website, order, options):
        "Fix the issue of Odoo's search in html fields"
        with_image = options['displayImage']
        options = options.copy()
        options['displayDescription'] = False
        result = super()._search_get_detail(website, order, options)
        if with_image:
            result['mapping']['image_url'] = {'name': 'image_url', 'type': 'html'}

        # to fix Odoo's issue Odoo catagory is not multi website compatible
        result['base_domain'] = [website.website_domain()]

        return result
