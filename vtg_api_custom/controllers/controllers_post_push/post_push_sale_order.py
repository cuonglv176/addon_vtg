# -*- coding: utf-8 -*-
import requests
import json
from odoo.osv import expression
import urllib3
import certifi
import logging
from requests.auth import HTTPBasicAuth
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)
API_URL_PREFIX = '/vtg'

class ApiController(http.Controller):

    def invalid_respone(self, status, message):
        # Response.status = str(status)
        return {
            "message": message,
            "status": status,
        }

    @http.route(route=API_URL_PREFIX + '/sale_order_create', type='json', auth='public', methods=['POST'], website=True)
    def sale_order_create(self, **kwargs):
        return self.dispatch_request('sale_order_create')

    @http.route(route=API_URL_PREFIX + '/sale_order_create_shopify', type='json', auth='public', methods=['POST'], website=True)
    def sale_order_create_shopify(self, **kwargs):
        return self.dispatch_request('sale_order_create_shopify')

    def dispatch_request(self, action, **kw):
        if action == 'sale_order_create':
            return self.do_sale_order_create()
        if action == 'sale_order_create_shopify':
            return self.do_sale_order_create_shopify()
        return self.invalid_respone(404, "It seems to be no action was specified")

    def get_access_token(self):
        cr = http.request.cr
        headers = http.request.httprequest.headers
        access_token = headers.get('Authorization')
        query = """SELECT split_part(%s,' ', 2) as token"""
        cr.execute(query, (access_token,))
        res = cr.dictfetchone()
        return res['token']

    def do_sale_order_create(self):
        """."""
        params = http.request.jsonrequest
        sale_order_obj = request.env['sale.order'].sudo()
        sale_order_line_obj = request.env['sale.order.line'].sudo()
        product_obj = request.env['product.product'].sudo()

        if not params.get('partner_name'):
            return self.invalid_respone(404, "partner_name MISDIRECTED REQUEST")
        if not params.get('partner_phone'):
            return self.invalid_respone(404, "partner_phone MISDIRECTED REQUEST")

        partner_id = request.env['res.partner'].sudo().search(
            [('phone', '=', params.get('partner_phone').lower())], limit=1)
        if not partner_id:
            partner_id = request.env['res.partner'].sudo().create({
                'name': params.get('partner_name'),
                'phone': params.get('partner_phone'),
                'team_id': 6,
                # 'user_id': 36,
            })
        # Create sale order
        sale_order_id = sale_order_obj.sudo().create({
            'partner_id': partner_id.id,
            'partner_phone': params.get('partner_phone').lower(),
            'address': params.get('address'),
            'source_id': 25,
            'team_id': 12,
            'type_order': 'cod'
        })
        for order_line in params.get('order_line'):
            product_id = product_obj.search([('default_code','=',order_line.get('product_code'))])
            if product_id:
                sale_order_line_obj.create({
                    'product_id': product_id.id,
                    'product_uom_qty': order_line.get('product_uom_qty'),
                    'price_unit': order_line.get('price_unit'),
                    'order_id': sale_order_id.id,
                })

        return {
            "sale_order_id": sale_order_id.id,
            "sale_order_code": sale_order_id.name,
            "message": "Create sale order success",
            "status": 200
        }



    def do_sale_order_create_shopify(self):
        """."""
        params = http.request.jsonrequest
        sale_order_obj = request.env['sale.order'].sudo()
        sale_order_line_obj = request.env['sale.order.line'].sudo()
        product_obj = request.env['product.product'].sudo()

        phone = params.get('customer').get('phone')
        email = params.get('customer').get('email')
        first_name = params.get('customer').get('first_name')
        last_name = params.get('customer').get('last_name')
        address1 = params.get('customer').get('default_address').get('address1')
        address2 = params.get('customer').get('default_address').get('address2')
        city = params.get('customer').get('default_address').get('city')
        country_name = params.get('customer').get('default_address').get('country_name')
        address = str(address1) + ' ' + str(address2) + ' ' + str(city) + ' ' + str(country_name)

        partner_id = request.env['res.partner'].sudo().search(
            ['|',('phone', '=', phone),('email','=',email)], limit=1)
        if not partner_id:
            partner_id = request.env['res.partner'].sudo().create({
                'name': last_name + ' ' + first_name,
                'phone': phone or 'shopify no phone',
                'email': email or '',
            })
        # Create sale order
        sale_order_id = sale_order_obj.sudo().create({
            'partner_id': partner_id.id,
            'partner_phone': phone,
            'address': address,
            'source_id': 25,
            'team_id': 12,
            'type_order': 'cod'
        })
        for order_line in params.get('line_items'):
            product_id = product_obj.search([('default_code','=',order_line.get('sku'))])
            if product_id:
                sale_order_line_obj.create({
                    'product_id': product_id.id,
                    'product_uom_qty': order_line.get('quantity'),
                    'price_unit': order_line.get('price'),
                    'order_id': sale_order_id.id,
                })

        return {
            "message": "Create sale order success",
            "sale_order_id": sale_order_id.id,
            "status": 200
        }

