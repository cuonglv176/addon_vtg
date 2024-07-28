# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vtg_product_group_type_id = fields.Many2one('vtg.product.group.type', string='Nhóm kiểu')
    vtg_product_type_id = fields.Many2one('vtg.product.type.type', string='Loại kiểu')
    vtg_product_sole_id = fields.Many2one('vtg.product.sole', string='Đế')
    vtg_product_size_id = fields.Many2one('vtg.product.size', string='Size')
    vtg_product_color_id = fields.Many2one('vtg.product.color', string='Màu')
    vtg_product_id = fields.Many2one('product.product', string='Mẫu tóc')

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

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for item in self:
            item.status_transfer = 'cancel'
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    percent_for_workers = fields.Integer(string='Phần trăm cho thợ')
    ampunt_for_workers = fields.Float(string='Giá trị cho cho thợ chính')
    ampunt_for_sub_workers = fields.Float(string='Giá trị cho cho thợ phụ')


class ProductGroupType(models.Model):
    _name = 'vtg.product.group.type'

    name = fields.Char(string='Tên nhóm kiểu', required=True)
    code = fields.Char(string='Mã nhóm kiểu', required=True)


class ProductTypeType(models.Model):
    _name = 'vtg.product.type.type'

    name = fields.Char(string='Tên loại kiểu', required=True)
    code = fields.Char(string='Mã loại kiểu', required=True)


class ProductSole(models.Model):
    _name = 'vtg.product.sole'

    name = fields.Char(string='Tên đế', required=True)
    code = fields.Char(string='Mã đế', required=True)


class ProductSize(models.Model):
    _name = 'vtg.product.size'

    name = fields.Char(string='Tên Size', required=True)
    code = fields.Char(string='Mã Size', required=True)
    sole_ids = fields.Many2many('vtg.product.sole', string='Đế')


class ProductColor(models.Model):
    _name = 'vtg.product.color'

    name = fields.Char(string='Tên màu', required=True)
    code = fields.Char(string='Mã màu', required=True)
