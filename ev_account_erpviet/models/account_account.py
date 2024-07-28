# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAccountInherit(models.Model):
    _inherit = "account.account"

    active = fields.Boolean(string='Active', default=True)
    x_required_product = fields.Boolean('Required Product', default=False, tracking=True)
    x_required_analytic = fields.Boolean('Required Analytic Account', default=False, tracking=True)
    x_required_expense_item = fields.Boolean('Required Expense Item', default=False, tracking=True)
    x_required_partner = fields.Boolean('Required Partner', default=False, tracking=True)