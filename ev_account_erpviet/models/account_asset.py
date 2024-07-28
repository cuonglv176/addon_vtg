# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAssetInherit(models.Model):
    _inherit = "account.asset"
    _order = 'create_date desc'

