# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.osv import osv


class ObjectCost(models.Model):
    _name = 'object.cost'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Code')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    description = fields.Text('Description')
    product_ids = fields.One2many('object.cost.product', 'object_cost_id', 'Details')
    unfinished_expense_account_id = fields.Many2one('account.account', 'Unfinished Expense Account')
    cost_account_ids = fields.One2many('object.cost.account', 'object_cost_id', 'Cost Account')

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'Code must be unique!')
    ]


class ObjectCostProduct(models.Model):
    _name = 'object.cost.product'

    object_cost_id = fields.Many2one('object.cost', 'Object Cost', ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product')


class ObjectCostAccount(models.Model):
    _name = 'object.cost.account'

    object_cost_id = fields.Many2one('object.cost', 'Object Cost', ondelete='cascade')
    account_id = fields.Many2one('account.account', 'Account')
    cost_factor_id = fields.Many2one('cost.factor', 'Cost Factor')

