# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    vtg_product_group_type_id = fields.Many2one('vtg.product.group.type', string='Nhóm kiểu')
    vtg_product_type_id = fields.Many2one('vtg.product.type.type', string='Loại kiểu')
    vtg_product_sole_id = fields.Many2one('vtg.product.sole', string='Đế')
    vtg_product_size_id = fields.Many2one('vtg.product.size', string='Size')
    vtg_product_color_id = fields.Many2one('vtg.product.color', string='Màu')
    vtg_product_id = fields.Many2one('product.product', string='Mẫu tóc')
    transfer_code = fields.Char('Mã vận đơn')
    transfer_status = fields.Selection([('not_created', 'Chưa tạo'), ('deliver', 'Đang vận chuyển'), ('done', 'Đã về')],
                                       'Trạng thái vận đơn')

    # def compute_transfer_status(self):
    #     for item in self:
    #         status = 'not_created'
    #         if all([picking_state in ('done', 'cancel') for picking_state in item.picking_ids.mapped('state')]):
    #             status = 'done'
    #         if any([picking_state in ('draft', 'waiting', 'confirmed', 'assigned') for picking_state in
    #                 item.picking_ids.mapped('state')]):
    #             status = 'deliver'
    #         item.transfer_status = status

    @api.onchange('vtg_product_group_type_id', 'vtg_product_type_id', 'vtg_product_sole_id', 'vtg_product_size_id',
                  'vtg_product_color_id')
    def onchange_product_chose(self):
        if self.vtg_product_group_type_id and self.vtg_product_type_id and self.vtg_product_sole_id and self.vtg_product_size_id and self.vtg_product_color_id:
            default_code = self.vtg_product_group_type_id.code + '-' + self.vtg_product_type_id.code + '-' + self.vtg_product_sole_id.code + '-' + self.vtg_product_size_id.code + '-' + self.vtg_product_color_id.code
            product_id = self.env['product.product'].search([('default_code', '=', default_code)])
            self.vtg_product_id = product_id

    def action_add_product(self):
        if self.vtg_product_id:
            self.order_line.create({
                'name': self.vtg_product_id.name,
                'product_id': self.vtg_product_id.id,
                'product_uom_qty': 1,
                'product_uom': self.vtg_product_id.uom_id.id,
                'price_unit': self.vtg_product_id.lst_price,
                'order_id': self.id,
            })


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    price_unit_currency = fields.Float(string="Đơn giá ngoại tệ", digits=0)
    exchange_rate = fields.Float(string="Tỉ giá (VNĐ)", digits=0)

    @api.onchange('price_unit_currency', 'exchange_rate')
    def onchange_exchange_rate(self):
        if self.price_unit_currency and self.exchange_rate:
            self.price_unit = self.price_unit_currency * self.exchange_rate