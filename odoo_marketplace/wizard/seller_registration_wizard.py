# -*- coding: utf-8 -*-
##########################################################################
# 2010-2017 Webkul.
#
# NOTICE OF LICENSE
#
# All right is reserved,
# Please go through this link for complete license : https://store.webkul.com/license.html
#
# DISCLAIMER
#
# Do not edit or add to this file if you wish to upgrade this module to newer
# versions in the future. If you wish to customize this module for your
# needs please refer to https://store.webkul.com/customisation-guidelines/ for more information.
#
# @Author		: Webkul Software Pvt. Ltd. (<support@webkul.com>)
# @Copyright (c) : 2010-2017 Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# @License	   : https://store.webkul.com/license.html
#
##########################################################################


from odoo import models,fields,api,http
from odoo.http import request
from ast import literal_eval

import json
import urllib

import logging
_logger = logging.getLogger(__name__)

class SellerConfirmation(models.TransientModel):
	_name="seller.resistration.wizard"
	_description = "Seller Resistration Wizard"

	@api.model
	def default_get(self,default_fields):
		res = super(SellerConfirmation,self).default_get(default_fields)
		resConfig = self.env['res.config.settings']
		partner_id = self.env['res.partner'].browse(self._context.get('active_id'))
		res['partner_name_one'] = partner_id.name
		res['partner_name_two'] = partner_id.name
		res['partner_id'] = partner_id.id
		res['user_id'] = self._context.get("user_id", False)
		if resConfig.get_mp_global_field_value("auto_approve_seller"):
			res['auto_approve_seller'] = True
		if resConfig.get_mp_global_field_value("mp_auto_approve_qty"):
			res['auto_approve_qty']	= True
		if resConfig.get_mp_global_field_value("mp_auto_product_approve"):
			res['auto_product_approve'] = True
		return res

	auto_product_approve = fields.Boolean(string="Auto Product Approve")
	auto_approve_qty = fields.Boolean(string="Auto Quantity Approve")
	auto_approve_seller = fields.Boolean(string="Auto Seller Approve")
	partner_id = fields.Many2one("res.partner")
	user_id = fields.Many2one("res.users")
	partner_name_one = fields.Char()
	partner_name_two = fields.Char()


	def get_seller_profile(self):
		var_url = '/web#id='+ str(self.partner_id.id) + '&view_type=form&model=res.partner&menu_id='+str(self.env.ref('odoo_marketplace.wk_seller_dashboard').id)+'&action='+str(self.env.ref('odoo_marketplace.wk_seller_action').id)
		return {'type': 'ir.actions.act_url',
				'name': "Sellers",
				'target': 'new',
				'url': var_url,
		}

	def confirm_customer_as_seller(self):
		try:
			current_user_id = self.user_id
			partner_id = self.partner_id
			if not current_user_id:
				values = {
						'name':partner_id.name,
						'login':partner_id.email,
						'partner_id':partner_id.id,
					}
				IrConfigParam = self.env['ir.config_parameter']
				template_user_id = literal_eval(IrConfigParam.get_param('base.template_portal_user_id', 'False'))
				template_user = self.env['res.users'].browse(template_user_id)
				assert template_user.exists(), 'Signup: invalid template user'

				values['active'] = True
				current_user_id = template_user.with_context(no_reset_password=True).copy(values)

			wk_valse = {
				"payment_method": [(6, 0, current_user_id.partner_id._set_payment_method())],
				"commission": self.env['ir.default'].get('res.config.settings', 'mp_commission'),
				"location_id": self.env['ir.default'].get('res.config.settings', 'mp_location_id', company_id=True) or False,
				"warehouse_id": self.env['ir.default'].get('res.config.settings', 'mp_warehouse_id', company_id=True) or False,
				"auto_product_approve": self.auto_product_approve,
				"seller_payment_limit": self.env['ir.default'].get('res.config.settings', 'mp_seller_payment_limit'),
				"next_payment_request": self.env['ir.default'].get('res.config.settings', 'mp_next_payment_request'),
				"auto_approve_qty": self.auto_approve_qty,
				"url_handler" : partner_id.id,
				"seller" : True,
			}
			current_user_id.partner_id.write(wk_valse)
			draft_seller_group_id = self.env['ir.model.data'].check_object_reference('odoo_marketplace', 'marketplace_draft_seller_group')[1]
			groups_obj = self.env["res.groups"].browse(draft_seller_group_id)
			if groups_obj:
				for group_obj in groups_obj:
					group_obj.sudo().write({"users": [(4, current_user_id.id, 0)]})

			if self.auto_approve_seller:
				current_user_id.partner_id.write({
				'state' : "approved"
				})

			if not self.user_id:
				current_user_id.action_reset_password()
			current_user_id.notification_on_partner_as_a_seller()

			partner_name = current_user_id.name
		except Exception as e:
			_logger.info("~~~~~~~~~~~Exception~~~~~~~~~~%r~~~~~~~~~~~~",e)
		return {
			'name':'Confirmation',
			'type':'ir.actions.act_window',
			'res_model':'seller.resistration.wizard',
			'view_mode':'form',
			'binding_view_types':'form',
			'res_id' : self.id,
			'view_id':self.env.ref('odoo_marketplace.registration_completed_wizard_form').id,
			'context' : {'auto_approve_seller':self.auto_approve_seller,},
			'target':'new',
		}
