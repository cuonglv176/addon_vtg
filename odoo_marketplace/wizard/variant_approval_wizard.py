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
import logging
_logger = logging.getLogger(__name__)

class VariantApprovalWizard(models.TransientModel):
    _name = 'variant.approval.wizard'
    _description = "Product Variant Approval Wizard"

    @api.model
    def default_get(self, default_fields):
        res = super(VariantApprovalWizard,self).default_get(default_fields)
        product_id = self.env['product.template'].browse(self._context.get('active_id'))
        res['product_id'] = product_id.id
        res['variant_ids'] = [(6, 0, product_id.product_variant_ids.ids)]
        return res

    product_id = fields.Many2one("product.template", string="Product")
    variant_ids = fields.Many2many("product.product", string="Seller")

    def approve_selected_variant(self):
        product_id = self.product_id
        product_id.sudo().write({"status": "approved", "sale_ok": True})
        product_id.check_state_send_mail()
        if not product_id.is_initinal_qty_set and len(product_id.product_variant_ids) == 1:
            product_id.set_initial_qty()
        if self.variant_ids:
            self.variant_ids.set_to_approved()
        return True
