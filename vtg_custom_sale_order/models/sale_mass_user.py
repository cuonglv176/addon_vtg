# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleMassUser(models.TransientModel):
    _name = 'sale.order.user.mass'
    _description = 'assign user to sale (in mass)'

    @api.model
    def default_get(self, fields):

        """ Allow support of active_id / active_model instead of jut default_lead_id
        to ease window action definitions, and be backward compatible. """
        result = super(SaleMassUser, self).default_get(fields)

        if not result.get('sale_ids') and self.env.context.get('active_ids'):
            result['sale_ids'] = self.env.context.get('active_ids')
        return result

    sale_id = fields.Many2one('sale.order',required=False)
    sale_ids = fields.Many2many(
        'sale.order', 'sale_order_mass_user_rel',
        string='Active sale order', context={'active_test': False},
        default=lambda self: self.env.context.get('active_ids', []),
    )
    user_id = fields.Many2one('res.users', string='Nhân viên kinh doanh')
    team_id = fields.Many2one('crm.team', string='Nhóm bán hàng')

    force_assignment = fields.Boolean(default=False)

    def action_apply(self):
        """ """
        result_sales = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for sale_id in result_sales:
            sale_id.write({
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
            })
