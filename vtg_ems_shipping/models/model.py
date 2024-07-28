# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import requests
import json
import re
import logging

_logger = logging.getLogger(__name__)

url_ems = 'http://ws.ems.com.vn'
merchant_token = 'e981c8eabf482493546dae1ba7ce53bd'


def no_accent_vietnamese(s):
    s = s.decode('utf-8')
    s = re.sub(u'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(u'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
    s = re.sub(u'èéẹẻẽêềếệểễ', 'e', s)
    s = re.sub(u'ÈÉẸẺẼÊỀẾỆỂỄ', 'E', s)
    s = re.sub(u'òóọỏõôồốộổỗơờớợởỡ', 'o', s)
    s = re.sub(u'ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ', 'O', s)
    s = re.sub(u'ìíịỉĩ', 'i', s)
    s = re.sub(u'ÌÍỊỈĨ', 'I', s)
    s = re.sub(u'ùúụủũưừứựửữ', 'u', s)
    s = re.sub(u'ƯỪỨỰỬỮÙÚỤỦŨ', 'U', s)
    s = re.sub(u'ỳýỵỷỹ', 'y', s)
    s = re.sub(u'ỲÝỴỶỸ', 'Y', s)
    s = re.sub(u'Đ', 'D', s)
    s = re.sub(u'đ', 'd', s)
    return s.encode('utf-8')

class EmsWards(models.Model):
    _name = 'ems.wards'

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    district_code = fields.Char(string='District code')
    province_code = fields.Char(string='Province code')
    slug_name = fields.Char(string='Slug name')
    district_id = fields.Many2one('ems.district', string='Quận huyện')

class EmsDistrict(models.Model):
    _name = 'ems.district'

    description = fields.Char(string='Description')
    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    province_code = fields.Char(string='Province code')
    slug_name = fields.Char(string='Slug name')
    state_id = fields.Many2one('res.country.state', string='Tỉnh thành')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    log_ems = fields.Text('Log EMS')
    wards_ems_id = fields.Many2one('ems.wards', string='Xã phường')
    district_ems_id = fields.Many2one('ems.district', string='Quận huyện')
    logistics = fields.Selection([
        ('viettel', 'Viettel'),
        ('ems','EMS'),
    ], 'Đơn vị vận chuyển', default='ems')
    picking_policy = fields.Selection([
        ('direct', 'As soon as possible'),
        ('one', 'When all products are ready')],
        string='Shipping Policy', required=True, readonly=True, default='one',
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}
        , help="If you deliver all products at once, the delivery order will be scheduled based on the greatest "
               "product lead time. Otherwise, it will be based on the shortest.")

    def action_calculate_ems_shipping_price(self):
        branch_merchant_token = self.x_branch_id.ems_token
        if not branch_merchant_token:
            raise ValidationError("Vui lòng cấu hình ems token cho chi nhánh %s" % self.x_branch_id.name)
        url = url_ems + f'/api/v1/get-order-fee?merchant_token={branch_merchant_token}'
        headers = {
            'Content-Type': 'application/json'
        }
        payload = json.dumps({
            "from_province": self.x_branch_id.sent_state_id.ems_code,
            "from_district": self.x_branch_id.sent_district_id.ems_code,
            "to_address": self.address,
            "to_ward": self.wards_ems_id.code,
            "to_province": self.state_id.ems_code,
            "to_district": self.district_ems_id.code,
            "money_collect": self.amount_total,
            "total_quantity": 1,
            "total_weight": 1000,
            "service": 17,
        })
        response = requests.request("POST", url, headers=headers, data=payload).json()
        if response.get('code', False) == 'error':
            raise ValidationError(response.get('message', ''))
        data = response.get('data')
        self.total_shipping = data.get('fee').get('fee') + data.get('fee').get('remote_fee') + data.get('vas').get(
            'total_vas')

    def action_create_ems_shipping(self):
        branch_merchant_token = self.x_branch_id.ems_token
        if not branch_merchant_token:
            raise ValidationError("Vui lòng cấu hình ems token cho chi nhánh %s" % self.x_branch_id.name)
        url = url_ems + f'/api/v1/orders/create-v2?merchant_token={branch_merchant_token}'
        headers = {
            'Accept': 'application/javascript'
        }
        if not self.x_receiver_name or not self.x_receiver_phone:
            raise ValidationError("Vui lòng điền thông tin sdt, họ và tên người nhận!")
        payload = json.dumps({
            "order_code": self.name,
            "from_name": 'Bạch Hồng Đức',
            "from_phone": "0969141499",
            "from_province": self.x_branch_id.sent_state_id.ems_code,
            "from_district": self.x_branch_id.sent_district_id.ems_code,
            "from_ward": self.x_branch_id.sent_ward_id.ems_code,
            "from_address": self.x_branch_id.address,
            "to_name": self.x_receiver_name,
            "to_phone": self.x_receiver_phone,
            "to_province": self.state_id.ems_code or '',
            "to_district": self.district_ems_id.code or '',
            "to_ward": self.wards_ems_id.code or '',
            "to_address": self.address,
            # "product_name": "Tóc giả VTG",
            "product_name": "Phụ kiện thời trang",
            "total_amount": self.amount_total,
            "money_collect": self.amount_total + self.total_shipping,
            "total_quantity": 1,
            "total_weight": 100,
            "size": '0x0x0',
            "service": 14,
            "checked": True,
            "fragile": False,
            # "vas": ['cod'],
            "payment_config": False,
        })
        _logger.info(">>>>>>>>>>>>>>EMS>>>>>>>>>>>>..")
        _logger.info(payload)
        response = requests.request("POST", url, headers=headers, data=payload).json()
        _logger.info(response)
        self.log_ems = str(response) + '   v  '+ str(payload)
        if response.get('code', False) == 'error' and response.get('error_code', False) != '099':
            raise ValidationError(response.get('message', ''))
        self.transfer_code = response.get('data').get('tracking_code')


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    ems_code = fields.Char(string='EMS Code')
    ems_slug_name = fields.Char('Ems Slug Name')

    def action_sync_country_state(self):
        url = url_ems + f"/api/v1/address/province?merchant_token={merchant_token}"
        response = requests.get(url).json()
        for data in response.get('data'):
            self._cr.execute(f"""
                UPDATE res_country_state
                SET ems_code = '{data.get('code')}',
                    ems_slug_name = '{data.get('slug_name')}'
                WHERE convertTVkdau(name) = '{data.get('slug_name', '')}'
                AND ems_code IS NULL
            """)


class VtgDistrict(models.Model):
    _inherit = 'vtg.district'

    ems_code = fields.Char(string='EMS Code')
    ems_slug_name = fields.Char(string='EMS Slug Name')

    def action_sync_district(self):
        url = url_ems + f"/api/v1/address/district?merchant_token={merchant_token}"
        province_ids = self.env['res.country.state'].sudo().search([('ems_code', '!=', False)])
        sql = "INSERT INTO ems_district (description, code, name, province_code, slug_name)\nVALUES"
        for province_id in province_ids:
            payload = json.dumps({
                "province_code": province_id.ems_code
            })
            response = requests.get(url, data=payload).json()
            for data in response.get('data'):
                sql += f"\n('%s', '%s', '%s', '%s', '%s')," % (
                data.get('description'), data.get('code'), data.get('name'), data.get('province_code'),
                data.get('slug_name'))
                # sql += f"\n('{data.get('description')}', '{data.get('code')}', '{data.get('name')}', '{data.get('province_code')}', '{data.get('slug_name')}'),"
        _logger.info('sql: %s', sql[:-1])
        self._cr.execute(sql[:-1])


class VtgWards(models.Model):
    _inherit = 'vtg.wards'

    ems_code = fields.Char(string='EMS Code')
    ems_slug_name = fields.Char(string='EMS Slug Code')

    def action_sync_ward(self):
        url = url_ems + f"/api/v1/address/ward?merchant_token={merchant_token}"
        province_ids = self.env['res.country.state'].sudo().search([('ems_code', '!=', False)])
        sql = "INSERT INTO ems_wards (code, name, district_code, province_code, slug_name)\nVALUES"
        for province_id in province_ids:
            district_ids = self.env['vtg.district'].sudo().search([('state_id', '=', province_id.id)])
            for district_id in district_ids:
                payload = json.dumps({
                    "district_code": district_id.ems_code,
                    "province_code": province_id.ems_code
                })
                response = requests.get(url, data=payload).json()
                for data in response.get('data'):
                    sql += f"\n('%s', '%s', '%s', '%s', '%s')," % (
                        data.get('code'), data.get('name').replace("'", "''"), data.get('district_code'),
                        data.get('province_code'), data.get('slug_name').replace("'", "''"))
        _logger.info('sql: %s', sql[:-1])
        self._cr.execute(sql[:-1])

        # district_id = self.env['vtg.wards'].search(
        #     [('name', 'in', (name_1, name_2)), ('district_id', '=', district_id.id)])
        # if not district_id:
        #     raise ValidationError(
        #         'Vui cấu hình tên quận/huyện có tên: %s hoặc %s' % (name_1, name_2))
        # district_id.write({
        #     'ems_code': data.get('code'),
        #     'ems_slug_name': data.get('slug_name')
        # })
