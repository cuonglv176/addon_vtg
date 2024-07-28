# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _get_default_warehouse_id(self):
        res = super(ResUsers, self)._get_default_warehouse_id()
        if not self.env.user.x_branch_id:
            return res
        if self.property_warehouse_id:
            return self.property_warehouse_id
        return self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id), ('x_branch_id', '=', self.env.user.x_branch_id.id)], limit=1)
