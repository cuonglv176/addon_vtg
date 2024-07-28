# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    birthday = fields.Date(string='Ngày sinh')
    gender = fields.Selection([('male', 'Nam'), ('female', 'Nữ'), ('undefined', 'Không xác định')], default='undefined',
                              string='Giới tính')
    cv_link = fields.Html('CV Link')
    province = fields.Char('Tỉnh thành/Khu vực')
    channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh')
    vtg_channel_id = fields.Many2one('vtg.hr.channel', string='Kênh')
    vtg_source_id = fields.Many2one('vtg.hr.source', string='Nguồn', domain="[('channel_id', '=', vtg_channel_id)]")


class HrChannel(models.Model):
    _name = 'vtg.hr.channel'

    name = fields.Char(string='Tên kênh')
    note = fields.Text(string='Ghi chú')


class HrSource(models.Model):
    _name = 'vtg.hr.source'

    name = fields.Char(string='Tên ngồn')
    note = fields.Text(string='Mô tả')
    channel_id = fields.Many2one('vtg.hr.channel', string='Kênh')
