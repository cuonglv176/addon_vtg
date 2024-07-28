# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import requests
import json
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('viettel_post', 'Viettel Post')])
    token = fields.Char(string='ViettelPost - Aftership Token')
    slug_order = fields.Char(store=True)
    tracking_number_order = fields.Char(store=True)
    aftership_delivery_type = fields.Selection(string='Delivery Type',
                                               selection=[('pickup_at_store', 'Pickup At Store'),
                                                          ('pickup_at_courier', 'Pickup At Courier'),
                                                          ('door_to_door', 'Door To Door')])
    slug_type = fields.Selection(
        selection=[('fedex', 'FedEx'), ('usps', 'USPS'), ('ups', 'UPS'), ('dhl', 'DHL Express')],
        string='Slug Category')
    language = fields.Selection(string='Language', selection=[('vi', 'Vietnam'), ('en', 'English')])
    pickup_note = fields.Text(string='Pickup Note')
    delivery_id = fields.Many2one('stock.picking')
    sale_order_id = fields.Many2one('sale.order')


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    def button_confirm(self):
        viettelpost_method = self.env['delivery.carrier'].sudo().search([('delivery_type', '=', 'viettel_post')], limit=1)
        if viettelpost_method:
            token = viettelpost_method.token
        url = 'https://api.aftership.com/v4/trackings'
        headers = {
            'aftership-api-key': token,
            'Content-Type': 'application/json'
        }
        for records in self.order_id:
            for record in records.order_line:
                transfer_code = str(record.display_name.split(' -')[0][2:])
                pickup_note = self.carrier_id.pickup_note if self.carrier_id.pickup_note else ''
                language = self.carrier_id.language if self.carrier_id.language else ''
                if records.partner_invoice_id.street and records.partner_id.state_id and records.partner_id.country_id:
                    address = str(records.partner_invoice_id.street) + ' - ' + str(
                        records.partner_invoice_id.state_id.name) + ' - ' + str(
                        records.partner_invoice_id.country_id.name)
                else:
                    address = ''
                data = {
                    "tracking": {
                        "slug": self.carrier_id.slug_type,
                        "tracking_number": str(datetime.now().strftime('%y%m%d')) + transfer_code,
                        "title": "Transfer Order " + str(records.name),
                        "smses": records.partner_id.phone,
                        "emails": records.partner_id.email,
                        "order_id": records.name,
                        "custom_fields": {
                            "product_name": record.product_id.name,
                            "product_price": record.product_id.lst_price
                        },
                        "language": language,
                        "customer_name": records.partner_id.name,
                        "order_promised_delivery_date": str(
                            (records.date_order + timedelta(days=10)).strftime('%Y-%m-%d')),
                        "delivery_type": self.carrier_id.aftership_delivery_type,
                        "pickup_location": address,
                        "pickup_note": pickup_note
                    }
                }
                tracking_number = data['tracking']['tracking_number']
                slug = data['tracking']['slug']
                data_json = json.dumps(data, indent=4)
                data_json.replace(" ' ", ' " ')
                requests.post(url, data=data_json, headers=headers)
                records.slug_order = slug
                records.tracking_number_order = tracking_number
            res = super(ChooseDeliveryCarrier, self).button_confirm()
            return res
        else:
            res = super(ChooseDeliveryCarrier, self).button_confirm()
            return res
