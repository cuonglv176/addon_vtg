# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    user_id = fields.Many2one('res.users', string="Nhân viên")
    user_master_id = fields.Many2one('res.users', string="Thợ chính")
    user_assistant_id = fields.Many2one('res.users', string="Thợ phụ")
    commitions = fields.Many2one('res.users', string="Thợ phụ")

    def _export_for_ui(self, orderline):
        result = super()._export_for_ui(orderline)
        result['user_id'] = orderline.user_id[0]
        result['user_master_id'] = orderline.user_master_id[0]
        result['user_assistant_id'] = orderline.user_assistant_id[0]
        return result

    def _order_line_fields(self, line, session_id):
        result = super()._order_line_fields(line, session_id)
        vals = result[2]
        if vals.get('user_id', False):
            vals['user_id'] = vals['user_id']['id']
        if vals.get('user_master_id', False):
            vals['user_master_id'] = vals['user_master_id']['id']
        if vals.get('user_assistant_id', False):
            vals['user_assistant_id'] = vals['user_assistant_id']['id']
        return result
