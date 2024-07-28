# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transfer_status = fields.Selection([('not_created', 'Chưa tạo'), ('deliver', 'Đang vận chuyển'), ('done', 'Đã về')],
                                       'Trạng thái vận đơn', compute="_compute_transfer_status")

    def _compute_transfer_status(self):
        for item in self:
            item.transfer_status = item.purchase_id.transfer_status if item.purchase_id else None