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

from odoo import api, fields, models, _
from odoo.tools.translate import _

import logging
_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def signup(self, values, token=None):
        """ """
        context = dict(self._context)
        is_seller = values.get('is_seller')
        if is_seller:
            context["is_seller"] = is_seller
            values.pop("is_seller")
        return super(ResUsers, self.with_context(context)).signup(values, token)

    def copy(self, default=None):
        self.ensure_one()
        if self._context.get('is_seller', False):
            user_group = self.env.ref('base.group_user')
            default.update({
                'groups_id':[(6,0,[user_group.id])],
            })
        user_obj = super(ResUsers, self).copy(default=default)
        website = self._context.get('website_id', False)
        if website:
            website = self.env["website"].browse(int(website))
        if self._context.get('is_seller', False):
            # Set Default fields for seller (i.e: payment_methods, commission, location_id, etc...)
            wk_valse = {
                "payment_method": [(6, 0, user_obj.partner_id._set_payment_method())],
                "commission": self.env['ir.default'].get('res.config.settings', 'mp_commission'),
                "location_id": self.env['ir.default'].get('res.config.settings', 'mp_location_id', company_id=True) or False,
                "warehouse_id": self.env['ir.default'].get('res.config.settings', 'mp_warehouse_id', company_id=True) or False,
                "auto_product_approve": self.env['ir.default'].get('res.config.settings', 'mp_auto_product_approve'),
                "seller_payment_limit": self.env['ir.default'].get('res.config.settings', 'mp_seller_payment_limit'),
                "next_payment_request": self.env['ir.default'].get('res.config.settings', 'mp_next_payment_request'),
                "auto_approve_qty": self.env['ir.default'].get('res.config.settings', 'mp_auto_approve_qty'),
                "seller" : True,
            }
            user_obj.partner_id.write(wk_valse)
            # Add user to Pending seller group
            draft_seller_group_id = self.env['ir.model.data'].check_object_reference('odoo_marketplace', 'marketplace_draft_seller_group')[1]
            groups_obj = self.env["res.groups"].browse(draft_seller_group_id)
            if groups_obj:
                for group_obj in groups_obj:
                    group_obj.write({"users": [(4, user_obj.id, 0)]})
        return user_obj

    def notification_on_partner_as_a_seller(self):
        # Here Ids must be single user is
        for user_obj in self:
            if user_obj.partner_id.seller:
                template = self.env['mail.template']
                resConfig = self.env['res.config.settings']
                if resConfig.get_mp_global_field_value("enable_notify_admin_4_new_seller"):
                    # Notify to admin by admin on new seller creation
                    temp_id = resConfig.get_mp_global_field_value("notify_admin_4_new_seller_m_tmpl_id")
                    if temp_id:
                        template.browse(temp_id).send_mail(user_obj.partner_id.id, True)
                if resConfig.get_mp_global_field_value("enable_notify_seller_4_new_seller"):
                    # Notify to Seller by admin on new seller creation
                    temp_id = resConfig.get_mp_global_field_value("notify_seller_4_new_seller_m_tmpl_id")
                    if temp_id:
                        template.browse(temp_id).send_mail(user_obj.partner_id.id, True)

    def check_user_is_seller(self):
        self.ensure_one()
        seller_grp = 'odoo_marketplace.marketplace_seller_group'
        officer_grp = 'odoo_marketplace.marketplace_officer_group'
        if self.partner_id.seller and self.has_group(seller_grp) and not self.has_group(officer_grp):
            return True
        return False

    def check_user_is_draft_seller(self):
        self.ensure_one()
        draft_seller_grp = 'odoo_marketplace.marketplace_draft_seller_group'
        seller_grp = 'odoo_marketplace.marketplace_seller_group'
        if self.partner_id.seller and self.has_group(draft_seller_grp) and not self.has_group(seller_grp):
            return True
        return False

    def check_user_is_mp_officer(self):
        officer_grp = 'odoo_marketplace.marketplace_officer_group'
        if self.has_group(officer_grp):
            return True
        return False

    def check_user_is_draft_or_approved_seller(self):
        self.ensure_one()
        draft_seller_grp = 'odoo_marketplace.marketplace_draft_seller_group'
        officer_grp = 'odoo_marketplace.marketplace_officer_group'
        if self.partner_id.seller and self.has_group(draft_seller_grp) and not self.has_group(officer_grp):
            return True
        return False

    def is_marketplace_user(self):
        draft_seller_grp = 'odoo_marketplace.marketplace_draft_seller_group'
        if self.has_group(draft_seller_grp):
            return True
        return False
