# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime, date
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError
import logging
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)



class HrJOB(models.Model):
    _inherit = 'hr.job'

    department_get_lead_ids = fields.Many2many('hr.department', string='Lấy lead từ phòng ban')
    marketing_get_lead_ids = fields.Many2many('res.users', string='Lấy lead từ Marketing')
    source_get_lead_ids = fields.Many2many('utm.source', string='Lấy lead từ Nguồn')
    channel_get_lead_ids = fields.Many2many('crm.kpi.mkt.budget.channel', string='Lấy lead từ Kênh')

