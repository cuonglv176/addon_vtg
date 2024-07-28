# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json

url_viettel = 'https://partner.viettelpost.vn'
# url_viettel = 'https://partnerdev.viettelpost.vn'
import logging

_logger = logging.getLogger(__name__)


class Branch(models.Model):
    _inherit = 'vtg.branch'

    sent_state_id = fields.Many2one('res.country.state', string='Tỉnh / TP Gửi', domain="[('country_id', '=', 241)]")
    sent_district_id = fields.Many2one('vtg.district', string='Quận Huyện Gửi',
                                       domain="[('state_id', '=', sent_state_id)]")
    sent_ward_id = fields.Many2one('vtg.wards', string='Xã / Phường Gửi',
                                   domain="[('district_id', '=', sent_district_id)]")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state_id = fields.Many2one('res.country.state', string='Tỉnh / TP')
    district_id = fields.Many2one('vtg.district', string='Quận Huyện', domain="[('state_id', '=', state_id)]")
    wards_id = fields.Many2one('vtg.wards', string='Xã Phường', domain="[('district_id', '=', district_id)]")
    money_collection = fields.Monetary(string='Tiền COD', tracking=True)
    note_for_customer = fields.Char(string='Ghi chú cho khách', tracking=True)
    total_shipping = fields.Monetary(string='Tổng cước vận chuyển', tracking=True)
    log_viettel = fields.Text('Log Viettel', tracking=True)
    viettel_post_status = fields.Text('Trạng thái Viettel', tracking=True)
    status_transfer = fields.Selection(
        selection=[('new', 'Mới'),
                   ('check', 'Đã check'),
                   ('sent', 'Đang gửi hàng'),
                   ('delivery', 'Đang giao hàng'),
                   ('successful', 'Giao thành công'),
                   ('return', 'Hoàn'),
                   ('cancel', 'Hủy')
                   ], default='new',
        string='Trạng thái vận đơn', tracking=True)



    def get_token_viettel(self):
        url = url_viettel + "/v2/user/Login"
        payload = json.dumps({
            "USERNAME": "0969141499",
            "PASSWORD": "Pi15032017!"
        })
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload).json()
        if response.get('error', False):
            raise ValidationError(response.get('message', ''))
        return response.get('data').get('token')

    def action_calculate_shipping_price(self):
        token = self.get_token_viettel()
        url = url_viettel + "/v2/order/getPrice"
        payload = json.dumps({
            "PRODUCT_WEIGHT": 200,
            "PRODUCT_PRICE": self.amount_total,
            "MONEY_COLLECTION": self.money_collection,
            "ORDER_SERVICE_ADD": "",
            "ORDER_SERVICE": "VCBO",
            "SENDER_DISTRICT": self.x_branch_id.sent_district_id.id_viettel,
            "SENDER_PROVINCE": self.x_branch_id.sent_state_id.id_viettel,
            "RECEIVER_DISTRICT": self.district_id.id_viettel,
            "RECEIVER_PROVINCE": self.state_id.id_viettel,
            "PRODUCT_TYPE": "HH",
            "NATIONAL_TYPE": 1
        })
        _logger.info(payload)
        headers = {
            'Token': token,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        _logger.info(">>>>>>>>>>>>>>>>>>>>>>")
        _logger.info(response.json().get('data'))
        _logger.info(response.json())
        self.total_shipping = response.json().get('data').get('MONEY_TOTAL')

    @api.constrains("x_receiver_phone")
    def _check_receiver_phone(self):
        for rec in self:
            if rec.type_order == 'cod':
                if rec.x_receiver_phone and len(rec.x_receiver_phone) <= 10:
                    continue
                raise ValidationError("Vui lòng điền số điện thoại người nhận tối đa 10 ký tự")

    def action_create_shipping(self):
        token = self.get_token_viettel()
        url = url_viettel + "/v2/order/createOrderNlp"
        LIST_ITEM = []
        for line in self.order_line:
            if line.product_id.categ_id.id == 1:
                LIST_ITEM.append({
                    "PRODUCT_NAME": line.product_id.name,
                    "PRODUCT_QUANTITY": line.product_uom_qty,
                    "PRODUCT_PRICE": 0,
                    "PRODUCT_WEIGHT": 1000
                })
        if not self.x_receiver_name or not self.x_receiver_phone:
            raise ValidationError("Vui lòng điền thông tin sdt, họ và tên người nhận!")
        payload = json.dumps({
            "ORDER_NUMBER": self.name,
            # "SENDER_FULLNAME": self.user_id.partner_id.name,
            "SENDER_FULLNAME": 'Bạch Hồng Đức',
            "SENDER_ADDRESS": self.x_branch_id.address,
            "SENDER_PHONE": "0969141499",
            "RECEIVER_FULLNAME": self.x_receiver_name,
            "RECEIVER_ADDRESS": self.address,
            "RECEIVER_PHONE": self.x_receiver_phone,
            "RECEIVER_WARD": self.wards_id.id_viettel,
            "RECEIVER_DISTRICT": self.district_id.id_viettel,
            "RECEIVER_PROVINCE": self.state_id.id_viettel,
            "PRODUCT_NAME": "Phụ kiện thẩm mỹ",
            "PRODUCT_DESCRIPTION": self.note_for_customer,
            "PRODUCT_QUANTITY": 1,
            "PRODUCT_PRICE": self.amount_total,
            "PRODUCT_WEIGHT": 100,
            "PRODUCT_LENGTH": 0,
            "PRODUCT_WIDTH": 0,
            "PRODUCT_HEIGHT": 0,
            "ORDER_PAYMENT": 3,
            "ORDER_SERVICE": "LCOD",
            "ORDER_SERVICE_ADD": None,
            "ORDER_NOTE": self.note_for_customer,
            "MONEY_COLLECTION": self.amount_total,
            "CHECK_UNIQUE": True,
            "LIST_ITEM": [
                LIST_ITEM
            ]
        })
        headers = {
            'Token': token,
            'Content-Type': 'application/json',
            'Cookie': 'SERVERID=A; SERVERID=B'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        self.log_viettel = response.json()
        _logger.info(">>>>>>>>>>>>>>>")
        _logger.info(response.json())
        if response.json().get('error', False):
            raise ValidationError(response.json().get('message'))
        self.transfer_code = response.json().get('data').get('ORDER_NUMBER')
