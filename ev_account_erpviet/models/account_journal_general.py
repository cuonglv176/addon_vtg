# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class AccountJournalGeneral(models.Model):
    _name = 'account.journal.general'

    def _default_company(self):
        return self.env.company.id

    @api.model
    def _get_currency(self):
        currency = False
        context = self._context or {}
        if context.get('default_journal_id', False):
            currency = self.env['account.journal'].browse(context['default_journal_id']).currency_id
        return currency

    name = fields.Char(string="Name")
    debit_partner_id = fields.Many2one('res.partner', string="Debit Partner", index=True)
    credit_partner_id = fields.Many2one('res.partner', string="Credit Partner",index=True)
    journal_id = fields.Many2one('account.journal', string="Journal",index=True)
    debit_acc_id = fields.Many2one('account.account', string="Debit Account",index=True)
    credit_acc_id = fields.Many2one('account.account', string="Credit Account",index=True)
    product_id = fields.Many2one('product.product', string="Product",index=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure",index=True)
    qty = fields.Float(string="Quantity")
    value = fields.Monetary(default=0.0, currency_field='company_currency_id', string="Value")
    date = fields.Date(string="Date",index=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], default='draft', string="State",index=True)
    account_move_id = fields.Many2one('account.move', string="Account Move Ref",index=True, ondelete="cascade")
    #Default group
    company_id = fields.Many2one('res.company', 'Company', default=_default_company,index=True)
    debit_analytic_account_id = fields.Many2one('account.analytic.account', 'Debit Analytic Account',index=True)
    credit_analytic_account_id = fields.Many2one('account.analytic.account', 'Credit Analytic Account',index=True)
    debit_object_cost_id = fields.Many2one('object.cost', 'Debit Object Cost',index=True)
    credit_object_cost_id = fields.Many2one('object.cost', 'Credit Object Cost',index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    amount_currency = fields.Monetary(default=0.0,
                                      help="The amount expressed in an optional other currency if it is a multi-currency entry.")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency",
                                          readonly=True,
                                          help='Utility field to express amount currency', store=True,index=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_currency,
                                  help="The optional other currency if it is a multi-currency entry.",index=True)

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id.id:
            self.uom_id = self.product_id.uom_id.id