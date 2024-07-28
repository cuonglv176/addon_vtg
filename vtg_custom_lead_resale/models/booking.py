# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import urllib3
import certifi
from datetime import date, datetime, timedelta


class CRM_Booking_Inherit(models.Model):
    _inherit = 'crm.lead.booking'

    type_lead = fields.Selection(selection=[('sale', 'SALE'), ('resale', 'RESALE')],
                                 string='Loại lead', default='sale')
