# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import requests
import json
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockReturnPickingInherit(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def _default_get_is_have_token(self):
        """Add the company of the parent as default if we are creating a child partner."""
        have_token = self.env['ir.config_parameter'].sudo().get_param('integrate_shipping.is_token')
        if have_token:
            return True

    is_have_token = fields.Boolean(default=_default_get_is_have_token)

    def _compute_is_have_token(self):
        have_token = self.env['ir.config_parameter'].sudo().get_param('integrate_shipping.is_token')
        self.is_have_token = False
        if have_token:
            self.is_have_token = True

    aftership_delivery_type = fields.Selection(string='Delivery Type', selection=[('pickup_at_store', 'Pickup At Store'),
                                                                        ('pickup_at_courier', 'Pickup At Courier'),
                                                                        ('door_to_door', 'Door To Door')])
    language = fields.Selection(string='Language', selection=[('vi', 'Vietnam'), ('en', 'English')])
    slug_type = fields.Selection(
        selection=[('fedex', 'FedEx'), ('usps', 'USPS'), ('ups', 'UPS'), ('dhl', 'DHL Express')],
        string='Slug Category')
    pickup_note = fields.Text(string="Pickup Note")

    def create_returns(self):
        viettelpost_method = self.env['delivery.carrier'].sudo().search([('delivery_type', '=', 'viettel_post')],
                                                                        limit=1)
        if viettelpost_method:
            token = viettelpost_method.token
            url = 'https://api.aftership.com/v4/trackings'
            headers = {
                'aftership-api-key': token,
                'Content-Type': 'application/json'
            }
            for record in self:
                current_record = self.picking_id
                code = self.picking_id.name.split('/')
                return_code = code[2]
                return_code = return_code[1:]
                if current_record.picking_type_id.company_id.street and current_record.picking_type_id.company_id.state_id and current_record.picking_type_id.company_id.country_id:
                    address = str(current_record.picking_type_id.company_id.street) + ' - ' + str(
                        current_record.picking_type_id.company_id.state_id.name) + ' - ' + str(
                        current_record.picking_type_id.company_id.country_id.name)
                else:
                    address = ''
                pickup_note = record.pickup_note if record.pickup_note else ''
                language = record.language if record.language else ''
                data = {
                    "tracking": {
                        "slug": self.slug_type,
                        "tracking_number": str(datetime.now().strftime('%y%m%d')) + return_code,
                        "title": str(record.picking_id.origin),
                        "smses": current_record.partner_id.phone,
                        "emails": current_record.partner_id.email,
                        "order_id": current_record.name,
                        "custom_fields": {
                            "product_name": current_record.product_id.name,
                            "product_price": current_record.product_id.lst_price
                        },
                        "language": language,
                        "order_promised_delivery_date": str(
                            (current_record.date_done + timedelta(days=7)).strftime('%Y-%m-%d')),
                        "delivery_type": self.aftership_delivery_type,
                        "pickup_location": address,
                        "pickup_note": pickup_note
                    },
                }
                data_json = json.dumps(data, indent=4)
                data_json.replace(" ' ", ' " ')
                requests.post(url, data=data_json, headers=headers)
            res = super(StockReturnPickingInherit, self).create_returns()
            return res
        else:
            res = super(StockReturnPickingInherit, self).create_returns()
            return res
