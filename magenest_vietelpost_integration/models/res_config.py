# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettingToken(models.TransientModel):
    _inherit = 'res.config.settings'

    is_token = fields.Boolean(string='AfterShip API', store=True)
    token = fields.Char(string='Token')

    @api.model
    def get_values(self):
        res = super().get_values()
        res.update(
            is_token=self.env['ir.config_parameter'].sudo().get_param('integrate_shipping.is_token'),
            token=self.env['ir.config_parameter'].sudo().get_param('integrate_shipping.token'),
        )
        return res

    def set_values(self):
        super().set_values()
        param = self.env['ir.config_parameter'].sudo()

        field_is_token = True and self.is_token or False
        field_token = self.token and self.token or False

        if not field_is_token:
            field_token = None

        param.set_param('integrate_shipping.is_token', field_is_token)
        param.set_param('integrate_shipping.token', field_token)