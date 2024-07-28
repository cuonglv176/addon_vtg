# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import urllib3
import certifi

# import phonenumbers
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)


class CRMLEAD(models.Model):
    _inherit = 'crm.lead'

    type_lead = fields.Selection(selection=[('sale', 'SALE'), ('resale', 'RESALE')],
                                 string='Loại lead', default='sale')

    @api.model
    def create(self, vals):
        lead = super(CRMLEAD, self).create(vals)
        if lead.type_lead == 'resale':
            lead.team_id = 12
            if lead.user_id.sale_team_id.id != 12:
                lead.user_id = None
        return lead
