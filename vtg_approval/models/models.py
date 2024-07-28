# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class ApprovalRequset(models.Model):
    _inherit = 'approval.request'

    vtg_product_group_type_id = fields.Many2one('vtg.product.group.type', string='Nhóm kiểu')
    vtg_product_type_id = fields.Many2one('vtg.product.type.type', string='Loại kiểu')
    vtg_product_sole_id = fields.Many2one('vtg.product.sole', string='Đế')
    vtg_product_size_id = fields.Many2one('vtg.product.size', string='Size')
    vtg_product_color_id = fields.Many2one('vtg.product.color', string='Màu')
    vtg_product_id = fields.Many2one('product.product', string='Mẫu tóc')
    amount = fields.Float(string="Tổng tiền", compute="compute_amount", store=True)
    amount_pay = fields.Float(string="Tổng tiền")
    x_purchase_state = fields.Selection([
        ('ordered', 'Đã đặt hàng'),
        ('arriving', 'Hàng đang về'),
        ('arrived', 'Hàng đã về'),
        ('arrived_part', 'Hàng đã về dở dang'),
        ('done', 'Hoàn thành'),
    ], string="Trạng thái hàng về")
    request_product_ids = fields.Many2many('product.product', string='Sản phẩm', compute="_compute_request_product",
                                           store=True)
    x_bank_holder = fields.Char('Chủ tài khoản')
    x_bank_account = fields.Char('Số tài khoản')
    x_bank = fields.Char('Ngân hàng')

    @api.depends('product_line_ids.product_id')
    def _compute_request_product(self):
        for item in self:
            item.request_product_ids = [(6, 0, item.product_line_ids.mapped('product_id').ids)]

    @api.depends('product_line_ids.x_price_total')
    def compute_amount(self):
        for item in self:
            item.amount = sum(item.product_line_ids.mapped('x_price_total'))

    @api.onchange('vtg_product_group_type_id', 'vtg_product_type_id', 'vtg_product_sole_id', 'vtg_product_size_id',
                  'vtg_product_color_id')
    def onchange_product_chose(self):
        if self.vtg_product_group_type_id and self.vtg_product_type_id and self.vtg_product_sole_id and self.vtg_product_size_id and self.vtg_product_color_id:
            default_code = self.vtg_product_group_type_id.code + '-' + self.vtg_product_type_id.code + '-' + self.vtg_product_sole_id.code + '-' + self.vtg_product_size_id.code + '-' + self.vtg_product_color_id.code
            product_id = self.env['product.product'].search([('default_code', '=', default_code)])
            self.vtg_product_id = product_id

    def action_add_product(self):
        if self.vtg_product_id:
            self.product_line_ids.create({
                'description': self.vtg_product_id.name,
                'product_id': self.vtg_product_id.id,
                'product_uom_id': self.vtg_product_id.uom_id.id,
                'approval_request_id': self.id,
            })

    def action_create_purchase_orders(self):
        """ Create and/or modifier Purchase Orders. """
        self.ensure_one()
        self.product_line_ids._check_products_vendor()

        for line in self.product_line_ids.filtered(lambda pl: not pl.product_id.x_is_expense):
            if not line.x_partner_id:
                raise ValidationError('Vui lòng chọn nhà cung cấp cho sản phẩm %s' % line.product_id.display_name)
            vendor = line.x_partner_id
            seller = line.product_id.seller_ids.filtered(lambda s: s.name.id == vendor.id)
            if not seller:
                seller = self.env['product.supplierinfo'].sudo().create({
                    'name': vendor.id,
                    'product_tmpl_id': line.product_id.product_tmpl_id.id,
                    'product_id': line.product_id.id
                })
            po_domain = line._get_purchase_orders_domain(vendor)
            purchase_orders = self.env['purchase.order'].search(po_domain)

            if purchase_orders:
                # Existing RFQ found: check if we must modify an existing
                # purchase order line or create a new one.
                purchase_line = self.env['purchase.order.line'].search([
                    ('order_id', 'in', purchase_orders.ids),
                    ('product_id', '=', line.product_id.id),
                    ('product_uom', '=', line.product_id.uom_po_id.id),
                ], limit=1)
                purchase_order = self.env['purchase.order']
                if purchase_line:
                    # Compatible po line found, only update the quantity.
                    line.purchase_order_line_id = purchase_line.id
                    purchase_line.product_qty += line.po_uom_qty
                    purchase_order = purchase_line.order_id
                else:
                    # No purchase order line found, create one.
                    purchase_order = purchase_orders[0]
                    po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                        line.product_id,
                        line.quantity,
                        line.product_uom_id,
                        line.company_id,
                        seller,
                        purchase_order,
                    )
                    new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                    new_po_line.update({
                        'price_unit': line.x_price_unit,
                        'taxes_id': line.x_tax_ids,
                        'price_subtotal': line.x_price_total,
                        'price_unit_currency': line.x_price_unit_currency,
                        'exchange_rate': line.x_exchange_rate,
                    })
                    line.purchase_order_line_id = new_po_line.id
                    purchase_order.order_line = [(4, new_po_line.id)]

                # Add the request name on the purchase order `origin` field.
                new_origin = set([self.name])
                if purchase_order.origin:
                    missing_origin = new_origin - set(purchase_order.origin.split(', '))
                    if missing_origin:
                        purchase_order.write({'origin': purchase_order.origin + ', ' + ', '.join(missing_origin)})
                else:
                    purchase_order.write({'origin': ', '.join(new_origin)})
            else:
                # No RFQ found: create a new one.
                po_vals = line._get_purchase_order_values(vendor)
                new_purchase_order = self.env['purchase.order'].create(po_vals)
                po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                    line.product_id,
                    line.quantity,
                    line.product_uom_id,
                    line.company_id,
                    seller,
                    new_purchase_order,
                )

                po_line_vals.update({
                    'price_unit': line.x_price_unit,
                    'taxes_id': line.x_tax_ids,
                    'price_subtotal': line.x_price_total,
                    'price_unit_currency': line.x_price_unit_currency,
                    'exchange_rate': line.x_exchange_rate,
                })
                new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                line.purchase_order_line_id = new_po_line.id
                new_purchase_order.order_line = [(4, new_po_line.id)]


class ApprovalProductLine(models.Model):
    _inherit = "approval.product.line"

    x_price_unit = fields.Float('Đơn giá')
    x_tax_ids = fields.Many2many('account.tax', string='Thuế')
    x_price_total = fields.Float('Thành tiền')
    x_price_unit_currency = fields.Float(string="Đơn giá ngoại tệ", digits=0)
    x_exchange_rate = fields.Float(string="Tỉ giá (VNĐ)", digits=0)
    x_partner_id = fields.Many2one('res.partner', 'Nhà cung cấp', domain=[('supplier_rank', '>', 0)])

    @api.onchange('product_id')
    def _onchange_product_get_partner(self):
        if self.product_id:
            last_po_id = self.env['purchase.order.line'].sudo().search([('product_id', '=', self.product_id.id)],
                                                                       order="create_date desc", limit=1)
            if last_po_id:
                last_partner_id = last_po_id.order_id.partner_id
            else:
                last_partner_id = self.product_id.seller_ids[0].name if self.product_id.seller_ids else None
            if last_partner_id:
                self.x_partner_id = last_partner_id.id

    @api.onchange('x_price_unit_currency', 'x_exchange_rate', 'quantity')
    def onchange_exchange_rate(self):
        if self.x_price_unit_currency and self.x_exchange_rate:
            self.x_price_unit = self.x_price_unit_currency * self.x_exchange_rate

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.x_tax_ids = self.product_id.supplier_taxes_id

    @api.onchange('x_price_unit', 'x_tax_ids')
    def onchange_price_unit(self):
        price_subtotal = self.x_price_unit * self.quantity
        price_tax = 0
        for tax_id in self.x_tax_ids:
            price_tax += tax_id._compute_amount(price_subtotal, price_unit=self.x_price_unit, quantity=self.quantity)
        self.x_price_total = price_subtotal + price_tax
