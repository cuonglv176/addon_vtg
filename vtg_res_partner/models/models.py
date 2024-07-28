# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    phone = fields.Char(required=True)
    x_partner_code = fields.Char(string='Mã KH (new)')

    @api.model
    def create(self, vals):
        partner_id = super(ResPartner, self).create(vals)
        if partner_id.customer_rank != 0:
            partner_id.x_partner_code = 'KH' + str(partner_id.id)
        elif partner_id.supplier_rank != 0:
            partner_id.x_partner_code = 'NCC' + str(partner_id.id)
        return partner_id
