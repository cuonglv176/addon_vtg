# -*- coding: utf-8 -*-
import requests
import json
from odoo import models, fields


def _update_tracking_url(slug, tracking_number):
    url = ''
    if slug and tracking_number:
        url = '{}/{}'.format(slug, tracking_number)
    return url


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    is_have_token = fields.Boolean(string='is have token')

    def _compute_is_have_token(self):
        have_token = self.env['ir.config_parameter'].sudo().get_param('integrate_shipping.is_token')
        self.is_have_token = False
        if have_token:
            self.is_have_token = True

    slug = fields.Char(related='stock_ids.slug_order', store=True)
    tracking_number = fields.Char(related='stock_ids.tracking_number_order', store=True)
    stock_ids = fields.One2many('delivery.carrier', 'delivery_id')

    def button_validate(self):
        viettelpost_method = self.env['delivery.carrier'].sudo().search([('delivery_type', '=', 'viettel_post')],
                                                                        limit=1)
        if viettelpost_method:
            token = viettelpost_method.token
            url = 'https://api.aftership.com/v4/trackings/{}/mark-as-completed'.format(
                _update_tracking_url(self.slug, self.tracking_number))
            headers = {
                'aftership-api-key': token,
                'Content-Type': 'application/json'
            }
            data = {
                "reason": "DELIVERED"
            }
            data_json = json.dumps(data, indent=4)
            data_json.replace(" ' ", ' " ')
            requests.post(url, data=data_json, headers=headers)
            res = super(StockPickingInherit, self).button_validate()
            return res
        else:
            res = super(StockPickingInherit, self).button_validate()
            return res

    def action_cancel(self):
        viettelpost_method = self.env['delivery.carrier'].sudo().search([('delivery_type', '=', 'viettel_post')],
                                                                        limit=1)
        if viettelpost_method:
            token = viettelpost_method.token
            url = 'https://api.aftership.com/v4/trackings/{}/mark-as-completed'.format(
                _update_tracking_url(self.slug, self.tracking_number))
            headers = {
                'aftership-api-key': token,
                'Content-Type': 'application/json'
            }
            data = {
                "reason": "LOST"
            }
            data_json = json.dumps(data, indent=4)
            data_json.replace(" ' ", ' " ')
            requests.post(url, data=data_json, headers=headers)
            res = super(StockPickingInherit, self).action_cancel()
            return res
        else:
            res = super(StockPickingInherit, self).action_cancel()
            return res
