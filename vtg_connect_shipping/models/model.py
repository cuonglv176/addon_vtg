# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api, _
import requests


class ResCountryState(models.Model):
    _inherit = 'res.country.state'

    id_viettel = fields.Integer(string='PROVINCE_ID')
    code_viettel = fields.Char(string='PROVINCE_CODE')


class VtgDistrict(models.Model):
    _name = 'vtg.district'

    id_viettel = fields.Integer(string='DISTRICT_ID')
    id_province_viettel = fields.Integer(string='PROVINCE_ID')
    value_viettel = fields.Char(string='DISTRICT_VALUE')
    name = fields.Char(string='DISTRICT_NAME')
    state_id = fields.Many2one('res.country.state', string='PROVINCE')

    def auto_create_district(self):
        state_ids = self.env['res.country.state'].search([('country_id', '=', 241)])
        district_obj = self.env['vtg.district']
        for state_id in state_ids:
            url = "https://partnerdev.viettelpost.vn/v2/categories/listDistrict?provinceId=" + str(state_id.id_viettel)
            payload = {}
            headers = {
                'Cookie': 'SERVERID=2'
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            datas = response.json().get('data')
            for data in datas:
                district_id = district_obj.search([('id_viettel', '=', data.get('DISTRICT_ID'))])
                if not district_id:
                    district_obj.create({
                        'id_viettel': data.get('DISTRICT_ID'),
                        'id_province_viettel': data.get('PROVINCE_ID'),
                        'value_viettel': data.get('DISTRICT_VALUE'),
                        'name': data.get('DISTRICT_NAME'),
                        'state_id': state_id.id,
                    })
                else:
                    district_id.write({
                        'id_province_viettel': data.get('PROVINCE_ID'),
                        'value_viettel': data.get('DISTRICT_VALUE'),
                        'name': data.get('DISTRICT_NAME'),
                        'state_id': state_id.id,
                    })


class VtgWards(models.Model):
    _name = 'vtg.wards'

    id_viettel = fields.Integer(string='WARDS_ID')
    id_district_viettel = fields.Integer(string='DISTRICT_ID')
    name = fields.Char(string='WARDS_NAME')
    district_id = fields.Many2one('vtg.district', string='DISTRICT')

    def auto_create_district(self):
        district_ids = self.env['vtg.district'].search([])
        wards_obj = self.env['vtg.wards']
        for district_id in district_ids:
            url = "https://partner.viettelpost.vn/v2/categories/listWards?districtId=" + str(district_id.id_viettel)
            payload = {}
            headers = {
                'Cookie': 'SERVERID=2'
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            datas = response.json().get('data')
            for data in datas:
                wards_id = wards_obj.search([('id_viettel', '=', data.get('WARDS_ID'))])
                if not wards_id:
                    wards_obj.create({
                        'id_viettel': data.get('WARDS_ID'),
                        'id_district_viettel': data.get('DISTRICT_ID'),
                        'name': data.get('WARDS_NAME'),
                        'district_id': district_id.id,
                    })
