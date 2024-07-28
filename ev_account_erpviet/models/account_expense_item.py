# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountExpenseItem(models.Model):
    _name = 'account.expense.item'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    code = fields.Char('Code')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(string='Active Account Expense Item', default=True)
