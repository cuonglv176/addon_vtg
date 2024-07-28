# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError


class VtgConfigSeting(models.Model):
    _name = 'vtg.config.setting'

    name = fields.Char(string='Tên cấu hình')
    day_recall_no_sale = fields.Integer(string='Số ngày thu hồi lead không phát sinh đơn hàng')
    day_recall_no_booking = fields.Integer(string='Số ngày thu hồi lead không phát booking')
    day_recall_no_care = fields.Integer(string='Số ngày thu hồi lead không cập nhật ghi chú')

    rate_sale = fields.Integer(string='Tỉ lệ sale')
    rate_mkt = fields.Integer(string='Lương marketing')
    rate_cost = fields.Integer(string='Tỉ lệ giá vốn')


