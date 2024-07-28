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

class MpWizardMessage(models.TransientModel):
    _name = "mp.wizard.message"
    _description = "MpWizardMessage"

    text = fields.Html(string='Message')

    def generated_message(self,message,name='Message/Summary'):
        partial_id = self.create({'text':message}).id
        return {
            'name':name,
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'mp.wizard.message',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
        }


class ServerActionWizard(models.TransientModel):
    _name = 'server.action.wizard'
    _description = "Server Action Wizard"

    @api.model
    def _get_products(self):
        result = self.env['product.template'].browse(
            self._context['active_ids'])
        return result.ids

    product_ids = fields.Many2many(
        "product.template", string="Products", default=_get_products)

    def approve_all_products(self):
        if self.product_ids:
            msg = "<p style='font-size: 15px'>Selected product(s) can't be approve, only pending product(s) will get approve.<p>"
            self.product_ids.approve_product()
            approved_products = self.product_ids.filtered(lambda o: o.status == "approved" and o.marketplace_seller_id)
            if approved_products:
                p_list = (', ').join(approved_products.mapped('name'))
                msg = "<p style='font-size: 15px'>Product(s) approved successfully: <strong>" + p_list + "</strong></p>"
            return self.env["mp.wizard.message"].generated_message(msg, "Approved Status")

    def reject_all_products(self):
        if self.product_ids:
            msg = "<p style='font-size: 15px'>Selected product(s) can't be reject.<p>"
            self.product_ids.reject_product()
            approved_products = self.product_ids.filtered(lambda o: o.status == "rejected" and o.marketplace_seller_id)
            if approved_products:
                p_list = (', ').join(approved_products.mapped('name'))
                msg = "<p style='font-size: 15px'>Product(s) rejected successfully: <strong>" + p_list + "</strong></p>"
            return self.env["mp.wizard.message"].generated_message(msg, "Reject Status")

class ServerActionWizardStock(models.TransientModel):
    _name = 'server.action.wizard.mp.stock'
    _description = "Server Action Wizard Mp Stock"

    @api.model
    def _get_marketplace_stocks(self):
        result = self.env['marketplace.stock'].browse(
            self._context['active_ids'])
        return result.ids

    marketplace_stock_ids = fields.Many2many(
        "marketplace.stock", string="Products", default=_get_marketplace_stocks)

    def approve_marketplace_stocks(self):
        if self.marketplace_stock_ids:
            self.marketplace_stock_ids.approve()

    def reject_marketplace_stocks(self):
        if self.marketplace_stock_ids:
            self.marketplace_stock_ids.reject()

class SellerReviewActionWizard(models.TransientModel):
    _name = 'seller.review.action.wizard'
    _description = "Seller Review Action Wizard"

    @api.model
    def _get_reviews(self):
        result = self.env['seller.review'].browse(
            self._context['active_ids'])
        return result.ids

    seller_review_ids = fields.Many2many(
        "seller.review", string="Reviews", default=_get_reviews)

    def publish_all_reviews(self):
        if self.seller_review_ids:
            self.seller_review_ids.website_publish_button()

    def unpublish_all_reviews(self):
        if self.seller_review_ids:
            self.seller_review_ids.website_unpublish_button()

class SellerRecommendationActionWizard(models.TransientModel):
    _name = 'seller.recommendation.action.wizard'
    _description = "Seller Recommendation Action Wizard"

    @api.model
    def _get_recommendations(self):
        result = self.env['seller.review'].browse(
            self._context['active_ids'])
        return result.ids

    seller_recommendation_ids = fields.Many2many("seller.recommendation", "wizard_id", "recommendation_id", string="Recommendations", default=_get_recommendations)

    def publish_all_recommendations(self):
        self.ensure_one()
        if self.seller_recommendation_ids:
            self.seller_recommendation_ids.write({"state" : 'pub'})

    def unpublish_all_recommendations(self):
        self.ensure_one()
        if self.seller_recommendation_ids:
            self.seller_recommendation_ids.write({"state" : 'unpub'})
