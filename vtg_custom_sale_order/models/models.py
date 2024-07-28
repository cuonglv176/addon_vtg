# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import urllib3
import certifi
from odoo.tools import float_is_zero, html_keep_url, is_html_empty

_logger = logging.getLogger(__name__)
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from werkzeug import urls

import random


class SaleOrderPaymentType(models.Model):
    _name = 'sale.order.type.payment'

    name = fields.Char(string='Hình thức thanh toán', required=True)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    type_payment_id = fields.Many2one('sale.order.type.payment', string='Hình thức thanh toán')
    date_invoice = fields.Date(string='Ngày hóa đơn')

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super()._prepare_invoice_values(order, name, amount, so_line)
        res['type_payment_id'] = self.type_payment_id.id
        res['invoice_date'] = self.date_invoice
        return res

    def _create_invoice(self, order, so_line, amount):
        if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (
                self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(_('The value of the down payment amount must be positive.'))

        amount, name = self._get_advance_details(order)

        invoice_vals = self._prepare_invoice_values(order, name, amount, so_line)

        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id

        invoice = self.env['account.move'].with_company(order.company_id) \
            .sudo().create(invoice_vals).with_user(self.env.uid)
        invoice.message_post_with_view('mail.message_origin_link',
                                       values={'self': invoice, 'origin': order},
                                       subtype_id=self.env.ref('mail.mt_note').id)
        invoice.action_post()
        # invoice.action_register_payment()
        return invoice


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_user_id = fields.Many2one('res.users', string='Nhân viên', compute='_get_user_sale_order_line', store=True)

    @api.depends('move_id.sale_id.order_line.user_id')
    def _get_user_sale_order_line(self):
        for s in self:
            if s.move_id.sale_id:
                for order_line in s.move_id.sale_id.order_line:
                    if order_line.product_id == s.product_id:
                        s.x_user_id = order_line.user_id
            else:
                s.x_user_id = None


class AccountMove(models.Model):
    _inherit = 'account.move'

    type_payment_id = fields.Many2one('sale.order.type.payment', string='Hình thức thanh toán')
    sale_id = fields.Many2one('sale.order', string='Tham chiếu đơn hàng', compute="_get_sale_order", store=True)
    date_order = fields.Date(string='Ngày đơn hàng', compute="_get_sale_order", store=True)
    amount_for_sale1 = fields.Monetary(string='Doanh thu được tính', compute="_get_amount_for_sale1", store=True)
    department_id = fields.Many2one('hr.department', string='Phòng', compute="_get_department_sale", store=True)
    type_customer = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', default='new', compute="auto_update_type_customer", store=True)
    marketing_id = fields.Many2one('res.users', string='Marketing', compute="_get_marketing_sale", store=True)

    @api.depends('sale_id')
    def _get_marketing_sale(self):
        for s in self:
            if s.sale_id:
                s.marketing_id = s.sale_id.marketing_id
            else:
                s.marketing_id = s.invoice_user_id

    @api.depends('sale_id.type_customer', 'pos_order_id.type_customer')
    def auto_update_type_customer(self):
        for s in self:
            if s.sale_id:
                s.type_customer = s.sale_id.type_customer
            if s.pos_order_id:
                s.type_customer = s.pos_order_id.type_customer

    @api.depends('user_id')
    def _get_department_sale(self):
        for s in self:
            if s.user_id:
                s.department_id = s.user_id.employee_id.department_id

    @api.depends('invoice_origin')
    def _get_sale_order(self):
        for s in self:
            if s.invoice_origin:
                s.sale_id = self.env['sale.order'].search([('name', '=', s.invoice_origin)])
                s.date_order = s.sale_id.date_order

    @api.depends('invoice_line_ids.price_subtotal', 'invoice_line_ids.product_id')
    def _get_amount_for_sale1(self):
        for s in self:
            amount_for_sale = 0
            if s.sale_id:
                if s.sale_id.type_order != 'cod':
                    if s.invoice_line_ids:
                        for line in s.invoice_line_ids:
                            if line.product_id.categ_id.id in (1, 2, 13):
                                amount_for_sale += line.price_subtotal
                            elif line.x_user_id.id == s.invoice_user_id.id:
                                amount_for_sale += line.price_subtotal
                        s.amount_for_sale1 = amount_for_sale

                if s.sale_id.type_order == 'cod':
                    if s.invoice_line_ids:
                        for line in s.invoice_line_ids:
                            if line.product_id.categ_id.id in (1, 2, 3, 4, 13):
                                amount_for_sale += line.price_subtotal
                        s.amount_for_sale1 = amount_for_sale
            elif s.pos_order_id:
                if s.invoice_line_ids:
                    for line in s.invoice_line_ids:
                        if line.product_id.categ_id.id in (1, 2, 13):
                            amount_for_sale += line.price_subtotal
                s.amount_for_sale1 = amount_for_sale


class CRMLEAD(models.Model):
    _inherit = 'crm.lead'

    sale_resale_id = fields.Many2one('sale.order', string='Đơn tham chiếu resale')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    ticket_id = fields.Many2one('helpdesk.ticket', string='Tham chiếu hô trợ')
    current_user = fields.Many2one('res.users', compute='_get_current_user')
    marketing_id = fields.Many2one('res.users', string='Marketing', compute="_get_marketing_sale", store=True)
    create_lead = fields.Datetime(string='Ngày tạo lead', compute="_get_marketing_sale", store=True)
    date_open_lead = fields.Datetime(string='Ngày giao lead', compute="_get_marketing_sale", store=True)
    department_id = fields.Many2one('hr.department', string='Phòng', compute="_get_department_sale", store=True)
    # channel_id = fields.Many2one('crm.kpi.mkt.budget.channel', string='Kênh', compute="depends_channel_id", store=True)
    #
    # @api.depends('source_id')
    # def depends_channel_id(self):
    #     for s in self:
    #         if s.source_id:
    #             s.channel_id = s.source_id.channel_id
    x_url_survey = fields.Char(string='URL khảo sát')
    x_receiver_phone = fields.Char('SĐT người nhận')
    x_receiver_name = fields.Char('Họ và tên người nhận')
    x_pos_order_code = fields.Char(string='Order code')

    @api.depends()
    def _get_current_user(self):
        for rec in self:
            rec.current_user = self.env.user
        # i think this work too so you don't have to loop
        self.update({'current_user': self.env.user.id})

    partner_phone = fields.Char(string='Số điện thoại', related='partner_id.phone')
    type_payment = fields.Selection(selection=[('cash', 'Tiền mặt'), ('transfer', 'Chuyển khoản'), ('pos', 'POS')],
                                    string='Hình thức thanh toán')
    address = fields.Text(string="Địa chỉ")
    transfer_code = fields.Char(string='Mã vận đơn tham chiếu')
    status_transfer = fields.Selection(
        selection=[('new', 'Mới'),
                   ('check', 'Đã check'),
                   ('sent', 'Đang gửi hàng'),
                   ('delivery', 'Đang giao hàng'),
                   ('successful', 'Giao thành công'),
                   ('return', 'Hoàn'),
                   ('cancel', 'Hủy')
                   ], default='new',
        string='Trạng thái vận đơn')
    type_payment_ids = fields.Many2many('sale.order.type.payment', string='Hình thức thanh toán')
    type_order = fields.Selection(selection=[('direct', 'Trực tiếp'),
                                             ('cod', 'Ship COD'),
                                             ('ship', 'Ship nội thành'),
                                             ('deposit', 'Khách cọc')
                                             ],
                                  string='Loại đơn hàng', default='direct')
    master_employee_id = fields.Many2one('hr.employee', string='Thợ chính')
    assistant_employee_id = fields.Many2one('hr.employee', string='Thợ phụ')
    amount_pay = fields.Float(string="Đã thanh toán", compute="_compute_amount_pay")
    amount_remain = fields.Float(string="Còn lại", compute="_compute_amount_pay")
    type_customer = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', default='new')
    history_transfer_ids = fields.One2many('sale.order.transfer.history', 'sale_id', string='Lịch sử cập nhật đơn COD')
    is_deposit = fields.Boolean(string='Đơn cọc', default=False)
    order_deposit_id = fields.Many2one('sale.order', string='Tham chiếu đơn cọc')
    status_selection = fields.Selection(
        [('high_forehead', 'Trán cao'),
         ('bald_peak', 'Hói đỉnh'),
         ('thinning_hair', 'Tóc thưa'),
         ('whole_head', 'Rụng Cả Đầu'),
         ('other', 'Không xác định')
         ], string="Tình trạng")

    def convert_pos_order_to_sale_order(self):
        order_ids = self.env['pos.order'].search(
            [('state', 'in', ('done', 'paid', 'invoiced')), ('create_date', '>', '2023-10-30')])
        for order_id in order_ids:
            lead_id = None
            if not order_id.booking_id.lead_id:
                lead_id = self.env['crm.lead'].search(
                    [('phone', '=', order_id.partner_id.phone), ('user_id', '=', order_id.user_id.id)], limit=1).id
            else:
                lead_id = order_id.booking_id.lead_id.id
            sale_order = self.env['sale.order'].create({
                'partner_id': order_id.partner_id.id,
                'date_order': order_id.date_order,
                'name': order_id.name,
                'origin': order_id.name,
                'x_branch_id': order_id.create_uid.x_branch_id.id,
                'type_order': 'direct',
                'marketing_id': order_id.marketing_id.id,
                'user_id': order_id.user_id.id,
                'team_id': order_id.user_id.sale_team_id.id,
                'source_id': order_id.source_id.id,
                'channel_id': order_id.channel_id.id,
                'booking_id': order_id.booking_id.id,
                'x_pos_order_code': order_id.name,
                'state': 'done',
                'create_date': order_id.create_date,
                'create_uid': order_id.create_uid.id,
                'opportunity_id': lead_id
                # Thêm thông tin khác tùy thuộc vào yêu cầu của bạn
            })
            # name, origin, state, date_order, partner_id, x_branch_id, type_order, amount_for_sale,
            # marketing_id, department_id, user_id, team_id, source_id, channel_id

            # Sao chép các sản phẩm từ đơn đặt hàng POS sang đơn hàng bán
            for line in order_id.lines:
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'price_unit': line.price_unit,
                })

    @api.onchange('type_order')
    def _onchange_is_deposit(self):
        for s in self:
            if s.type_order == 'deposit':
                product_id = self.env['product.product'].search([('default_code', '=', 'COC')])
                vals = {
                    'product_id': product_id.id,
                    'product_uom_qty': 1,
                    'product_uom': product_id.uom_id.id,
                    'name': product_id.name,
                    'user_id': None,
                }
                self.update({'order_line': [(0, 0, vals)]})
            else:
                s.order_line = None

    @api.depends('opportunity_id')
    def _get_marketing_sale(self):
        for s in self:
            if s.opportunity_id:
                s.marketing_id = s.opportunity_id.marketing_id
                s.create_lead = s.opportunity_id.create_date
                s.date_open_lead = s.opportunity_id.date_open
            else:
                s.marketing_id = s.user_id
                s.date_open_lead = s.date_order
                s.create_lead = s.date_order

    @api.depends('user_id')
    def _get_department_sale(self):
        for s in self:
            if s.user_id:
                s.department_id = s.user_id.employee_id.department_id

    def get_order_deposit(self, partner_id):
        order_deposit_id = self.env['sale.order'].sudo().search(
            [('partner_id', '=', partner_id.id),
             ('type_order', '=', 'deposit'),
             ('state', 'in', ('sale', 'done'))], limit=1)
        invoice_id = self.env['account.move'].sudo().search([('sale_id', '=', order_deposit_id.id)])
        order = self.env['sale.order'].sudo().search(
            [('order_deposit_id', '=', order_deposit_id.id),
             ('state', 'in', ('sale', 'done'))])
        if not order and invoice_id:
            return order_deposit_id
        else:
            return None

    @api.model
    def create(self, vals):
        sale_id = super(SaleOrder, self).create(vals)
        if sale_id.type_order != 'deposit':
            order_deposit_id = sale_id.get_order_deposit(sale_id.partner_id)
            if order_deposit_id:
                sale_id.order_deposit_id = order_deposit_id
                vals_order = {}
                for line_id in order_deposit_id.order_line:
                    if line_id.product_id.default_code == 'COC':
                        vals_order = {
                            'product_id': line_id.product_id.id,
                            'product_uom_qty': 1,
                            'price_unit': - line_id.price_unit,
                            'order_id': sale_id.id,
                        }
                self.update({'order_line': [(0, 0, vals_order)]})
        if not vals.get('opportunity_id'):
            if sale_id.source_id.id == 29 and sale_id.amount_total > 2000000:
                # initializing list
                teams = [12, 8, 15]
                teams_id = random.choice(teams)
                te_id = self.env['crm.team'].search([('id', '=', teams_id)])
                lead_id = self.env['crm.lead'].create({
                    'name': sale_id.partner_id.name,
                    'contact_name': sale_id.partner_id.name,
                    'phone': sale_id.partner_id.phone,
                    'source_id': sale_id.source_id.id,
                    'channel_id': sale_id.channel_id.id,
                    'status_selection': sale_id.status_selection,
                    'department_id': te_id.user_id.employee_id.department_id.id,
                    'marketing_id': sale_id.user_id.id,
                    'team_id': teams_id,
                    'sale_resale_id': sale_id.id,
                    'company_id': 1,
                    'type': 'lead',
                    'date_open': datetime.now(),
                    'date_input': datetime.today(),
                    'partner_id': sale_id.partner_id.id,
                    'street': sale_id.address,
                    'type_lead': 'resale',
                })
                sale_id.opportunity_id = lead_id
        #     if not sale_id.opportunity_id and sale_id.source_id.id != 29:
        #         lead_id = self.env['crm.lead'].sudo().search(
        #             [('phone', '=', sale_id.partner_id.phone), ('user_id', '=', sale_id.user_id.id)], limit=1)
        #         if not lead_id:
        #             lead_id = self.env['crm.lead'].create({
        #                 'name': sale_id.partner_id.name,
        #                 'contact_name': sale_id.partner_id.name,
        #                 'phone': sale_id.partner_id.phone,
        #                 'source_id': sale_id.source_id.id,
        #                 'channel_id': sale_id.channel_id.id,
        #                 'status_selection': sale_id.status_selection,
        #                 'department_id': sale_id.user_id.employee_id.department_id.id,
        #                 'marketing_id': sale_id.user_id.id,
        #                 'team_id': sale_id.user_id.sale_team_id.id,
        #                 'sale_resale_id': sale_id.id,
        #                 'company_id': 1,
        #                 'type': 'opportunity',
        #                 'date_open': datetime.now(),
        #                 'date_input': datetime.today(),
        #                 'partner_id': sale_id.partner_id.id,
        #                 'street': sale_id.address,
        #             })
        #         sale_id.opportunity_id = lead_id
        return sale_id

    def _auto_vang_lai(self):
        sale_ids = self.env['sale.order'].search(
            [('source_id', '=', 29), ('amount_total', '>', 3000000), ('opportunity_id', '=', False),
             ('date_order', '>=', '01/01/2024')])
        _logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        _logger.info(len(sale_ids))
        for sale_id in sale_ids:

            teams = [12, 8, 15]
            teams_id = random.choice(teams)
            te_id = self.env['crm.team'].search([('id', '=', teams_id)])
            if sale_id.partner_id.phone:
                lead_id = self.env['crm.lead'].create({
                    'name': sale_id.partner_id.name,
                    'contact_name': sale_id.partner_id.name,
                    'phone': sale_id.partner_id.phone,
                    'source_id': sale_id.source_id.id,
                    'channel_id': sale_id.channel_id.id,
                    'status_selection': sale_id.status_selection,
                    'department_id': te_id.user_id.employee_id.department_id.id,
                    'marketing_id': sale_id.user_id.id,
                    'team_id': teams_id,
                    'sale_resale_id': sale_id.id,
                    'company_id': 1,
                    'type': 'lead',
                    'date_open': datetime.now(),
                    'date_input': datetime.today(),
                    'partner_id': sale_id.partner_id.id,
                    'street': sale_id.address,
                    'type_lead': 'resale',
                })
                sale_id.opportunity_id = lead_id

    def write(self, vals):
        for sale_id in self:
            status_transfer_old = sale_id.status_transfer
            if sale_id.type_order != 'deposit':
                order_deposit_id = sale_id.get_order_deposit(sale_id.partner_id)
                if order_deposit_id:
                    vals.update({
                        'order_deposit_id': order_deposit_id.id
                    })
                    vals_order = {}
                    for line_id in order_deposit_id.order_line:
                        if line_id.product_id.default_code == 'COC':
                            vals_order = {
                                'product_id': line_id.product_id.id,
                                'product_uom_qty': 1,
                                'price_unit': - line_id.price_unit,
                                'order_id': sale_id.id,
                            }
                    a = 0
                    for line_id in sale_id.order_line:
                        if line_id.product_id.default_code == 'COC':
                            a = 1
                    if a == 0 and vals_order:
                        sale_id.order_line.create(vals_order)
            res = super(SaleOrder, self).write(vals)
            status_transfer_new = sale_id.status_transfer
            if status_transfer_old != status_transfer_new:
                self.env['sale.order.transfer.history'].create({
                    'date': datetime.now(),
                    'sale_id': sale_id.id,
                    'status_transfer_old': status_transfer_old,
                    'status_transfer_new': status_transfer_new
                })
        return res

    def unlink(self):
        partner_id = self.partner_id
        res = super(SaleOrder, self).unlink()
        self.auto_update_type_customer(partner_id)
        return res

    def auto_update_type_customer(self, partner_id):
        if partner_id:
            order_ids = self.env['sale.order'].sudo().search(
                [('partner_id', '=', partner_id.id), ('state', 'in', ('sale', 'done'))])
            for sale in order_ids:
                order = self.env['sale.order'].sudo().search(
                    [('partner_id', '=', sale.partner_id.id), ('date_order', '<', sale.date_order),
                     ('state', 'in', ('sale', 'done')), ('id', '!=', sale.id)])
                if order:
                    if order.order_line:
                        a = 0
                        for order_id in order_ids:
                            for line in order_id.order_line:
                                if line.product_id.categ_id.id == 1:
                                    a = 1
                        if a == 1:
                            sale.type_customer = 'old'
                        else:
                            sale.type_customer = 'new'
                    else:
                        sale.type_customer = 'new'
                else:
                    sale.type_customer = 'new'

    def auto_update_onchange_type_customer(self):
        date = datetime.now() - relativedelta(days=1)
        # sale_ids = self.env['sale.order'].search([('type_customer', '=', 'new'), ('create_date', '>=', date)])
        sale_ids = self.env['sale.order'].search(
            [('type_customer', '=', 'new'), ('create_date', '>=', '01/01/2024'), ('create_date', '<', '01/10/2024')])
        for sale_id in sale_ids:
            sale_id.update_onchange_type_customer()

    def update_onchange_type_customer(self):
        for sale in self:
            if sale.partner_id:
                query = """
                        SELECT a.name 
                        FROM sale_order a 
                        JOIN res_partner b ON a.partner_id = b.id
                        JOIN sale_order_line c on c.order_id = a.id
                        JOIN product_product d on d.id = c.product_id
                        JOIN product_template e on e.id = d.product_tmpl_id
                        WHERE b.id = %s
                        AND e.categ_id = 1
                        AND a.state in ('sale','done')
                    """
                self._cr.execute(query, (sale.partner_id.id,))
                sale_ids = self._cr.fetchall()
                type_customer = 'new'
                for sale_id in sale_ids:
                    if sale_id[0] != sale.name:
                        type_customer = 'old'
                sale.type_customer = type_customer

    @api.onchange('partner_id')
    def _onchange_type_customer(self):
        for sale in self:
            if sale.partner_id:
                query = """
                        SELECT a.name 
                        FROM sale_order a 
                        JOIN res_partner b ON a.partner_id = b.id
                        JOIN sale_order_line c on c.order_id = a.id
                        JOIN product_product d on d.id = c.product_id
                        JOIN product_template e on e.id = d.product_tmpl_id
                        WHERE b.id = %s
                        AND e.categ_id = 1
                        AND a.state in ('sale','done')
                    """
                self._cr.execute(query, (sale.partner_id.id,))
                sale_ids = self._cr.fetchall()
                type_customer = 'new'
                for sale_id in sale_ids:
                    if sale_id[0] != sale.name:
                        type_customer = 'old'
                sale.type_customer = type_customer

                # order = self.env['sale.order'].sudo().search(
                #     [('partner_id', '=', sale.partner_id.id), ('date_order', '<', sale.date_order)])
                # if order:
                #     if order.order_line:
                #         for line in order.order_line:
                #             if line.product_id.categ_id.id == 1:
                #                 sale.type_customer = 'old'
                #             else:
                #                 sale.type_customer = 'new'
                #     else:
                #         sale.type_customer = 'new'
                # else:
                #     sale.type_customer = 'new'
                if not sale.opportunity_id:
                    lead_ids = self.env['crm.lead'].sudo().search(
                        [('phone', '=', sale.partner_id.phone)])
                    for lead_id in lead_ids:
                        if lead_id.source_id:
                            sale.source_id = lead_id.source_id
            else:
                sale.type_customer = 'new'

    def _compute_amount_pay(self):
        for sale_id in self:
            invoices = sale_id.mapped('invoice_ids')
            amount_pay = 0
            for invoice in invoices:
                if invoice.state == 'posted':
                    amount_pay += invoice.amount_total
            sale_id.amount_pay = amount_pay
            sale_id.amount_remain = sale_id.amount_total - amount_pay

    def action_send_order_cod(self):
        users_ids = self.env['res.users'].search([('x_branch_id', '=', self.x_branch_id.id)])
        emails_to = 'nhungnt.hermanoss@gmail.com,'
        for users_id in users_ids:
            emails_to += users_id.login + ','
        subject = '[CHỜ SHIP] Đơn hàng COD: ' + self.name + ' khách hàng ' + self.partner_id.name
        body = _("""
                           Xin chào Nguyễn Thị Nhung,
                           
                           CC Chi nhánh: """ + self.x_branch_id.name + """,
    
                           Bạn có đơn chờ vận chuyển như sau:
                               Mã đơn hàng: """ + self.name + """
                               Khách hàng: """ + self.partner_id.name + """
                               Số điện thoại: """ + self.partner_id.phone + """
                               Địa chỉ: """ + str(self.address) + """
    
                           Chi tiết vui lòng truy cập: https://crm.hermanoss.com/web#id=""" + str(self.id) + """&menu_id=237&cids=1&action=356&model=sale.order&view_type=form
    
                           Thanks and best regards,
               """)
        email = self.env['ir.mail_server'].build_email(
            email_from=self.env.user.email,
            email_to=emails_to,
            subject=subject, body=body
        )
        # self.env['ir.mail_server'].send_email(email)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for so in self:
            so.opportunity_id.date_buy = so.date_order
            if so.type_order in ('cod', 'ship'):
                so.action_send_order_cod()
            so.auto_update_type_customer(so.partner_id)
        return res

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        - Sales Team
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        self = self.with_company(self.company_id)

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.context.get('default_user_id', self.env.uid)
        # if user_id and self.user_id.id != user_id:
        #     values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms'):
            if self.terms_type == 'html' and self.env.company.invoice_terms_html:
                baseurl = html_keep_url(self.get_base_url() + '/terms')
                values['note'] = _('Terms & Conditions: %s', baseurl)
            elif not is_html_empty(self.env.company.invoice_terms):
                values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.user_id.sale_team_id.id
        self.update(values)

    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.user_id:
            self.team_id = self.user_id.sale_team_id.id

    def action_auto_create_helpdesk(self, date_start=datetime.today(),
                                    date_end=datetime.today()):
        query1 = """
                    SELECT a.order_id
                    FROM sale_order_line a 
                    JOIN product_product b on a.product_id = b.id 
                    JOIN product_template c on b.product_tmpl_id = c.id
                    JOIN sale_order d on d.id = a.order_id
                    WHERE c.categ_id in (1) 
                    AND d.date_order >  %s ::date - INTERVAL '7 days'
                    AND d.date_order <  %s ::date + INTERVAL '2 days'
                    AND d.state in ('done', 'sale')
                """
        self._cr.execute(query1, (date_start, date_end))
        res1 = self._cr.fetchall()
        _logger.info("res1res1res1res1res1res1res1res1res1res1res1res1")
        _logger.info(res1)
        for sa_id in res1:
            sale_id = self.env['sale.order'].sudo().search([('id', '=', sa_id[0])])
            _logger.info("sale_idsale_idsale_idsale_idsale_idsale_idsale_idsale_idsale_id")
            _logger.info(sale_id)
            ticket_id = self.env['helpdesk.ticket'].search([('sale_id', '=', sale_id.id), ('type_care', '=', '3')])
            if not ticket_id:
                if sale_id.type_order == 'cod':
                    if sale_id.status_transfer == 'successful':
                        sale_id.create_helpdesk_ticket('3')
                else:
                    sale_id.create_helpdesk_ticket('3')
        query = """
            SELECT a.order_id
            FROM sale_order_line a 
            JOIN product_product b on a.product_id = b.id 
            JOIN product_template c on b.product_tmpl_id = c.id
            JOIN sale_order d on d.id = a.order_id
            WHERE c.categ_id in (1) 
            AND d.date_order >  %s::date - INTERVAL '37 days'
            AND d.date_order <  %s::date - INTERVAL '28 days'
            AND d.state in ('done', 'sale')
        """
        self._cr.execute(query, (datetime.today(), datetime.today()))
        res = self._cr.fetchall()
        _logger.info("????????????????????????????????????????????????????")
        _logger.info(res)
        for sa_id in res:
            sale_id = self.env['sale.order'].sudo().search([('id', '=', sa_id[0])])
            ticket_id = self.env['helpdesk.ticket'].search([('sale_id', '=', sale_id.id), ('type_care', '=', '30')])
            _logger.info(sale_id.name)
            _logger.info(sale_id.type_order)
            _logger.info(ticket_id)
            if not ticket_id:
                if sale_id.type_order == 'cod':
                    if sale_id.status_transfer == 'successful':
                        sale_id.create_helpdesk_ticket('30')
                else:
                    sale_id.create_helpdesk_ticket('30')

        # query1 = """
        #             SELECT a.order_id
        #             FROM sale_order_line a
        #             JOIN product_product b on a.product_id = b.id
        #             JOIN product_template c on b.product_tmpl_id = c.id
        #             JOIN sale_order d on d.id = a.order_id
        #             WHERE c.categ_id in (1)
        #             AND d.date_order >  %s::date - INTERVAL '180 days'
        #             AND d.date_order <  %s::date - INTERVAL '179 days'
        #             AND d.state in ('done', 'sale')
        #         """
        # self._cr.execute(query1, (date_start,date_end))
        # res1 = self._cr.fetchall()
        # for sa_id1 in res1:
        #     sale_id1 = self.env['sale.order'].sudo().search([('id', '=', sa_id1[0])])
        #     ticket_id1 = self.env['helpdesk.ticket'].search([('sale_id', '=', sale_id1.id), ('type_care', '=', '180')])
        #     if not ticket_id1:
        #         if sale_id1.type_order == 'cod':
        #             if sale_id1.status_transfer == 'successful':
        #                 sale_id1.create_helpdesk_ticket('180')
        #         else:
        #             sale_id1.create_helpdesk_ticket('180')

    def create_helpdesk_ticket(self, type_care):
        vals = {
            "name": "Chăm sóc sau bán đơn hàng " + self.name,
            "partner_name": self.partner_id.name,
            "partner_phone": self.partner_id.phone,
            "email": self.partner_id.email,
            "description": self.note,
            "team_id": 1,
            "ticket_type_id": 3,
            "partner_id": self.partner_id.id,
            "source_id": self.source_id.id,
            "sale_id": self.id,
            "type_care": type_care,
            "user_id": 68
        }
        _logger.info(vals)
        # create and add a specific creation message
        ticket_sudo = self.env['helpdesk.ticket'].sudo().create(vals)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    user_id = fields.Many2one('res.users', string="Nhân viên")
    user_master_id = fields.Many2one('res.users', string="Thợ chính")
    user_assistant_id = fields.Many2one('res.users', string="Thợ phụ")
    category_id = fields.Many2one('product.category', string="Nhóm sản phẩm", compute='_update_category_product',
                                  store=True)
    line_user_ids = fields.One2many('order.line.user', 'sale_line_id', 'Line Users')

    @api.constrains('product_id')
    def onchange_product_get_commission(self):
        if self.product_id:
            self.line_user_ids = None
            line_user_vals = []
            for commission_id in self.product_id.commission_config_ids:
                line_user_vals.append((0, 0, {
                    'type': commission_id.type,
                    'discount_type': commission_id.discount_type,
                    'discount': commission_id.discount,
                    'rate': commission_id.rate
                }))
            if line_user_vals:
                self.line_user_ids = line_user_vals

    def _compute_user(self):
        for item in self:
            employee_ids = item.line_user_ids.filtered(lambda l: l.type == 'employee')
            master_ids = item.line_user_ids.filtered(lambda l: l.type == 'master')
            assistant_ids = item.line_user_ids.filtered(lambda l: l.type == 'assistant')
            item.user_id = employee_ids[0].user_id if employee_ids else None
            item.user_master_id = master_ids[0].user_id if master_ids else None
            item.user_assistant_id = assistant_ids[0].user_id if assistant_ids else None

    def action_confirm_users(self):
        view = self.env.ref('vtg_custom_sale_order.sale_order_line_editable_view_form').sudo()
        return {
            'name': 'Chi tiết bán hàng',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id
        }

    @api.depends('product_id')
    def _update_category_product(self):
        for s in self:
            s.category_id = s.product_id.categ_id

    type_customer = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', default='new', compute="_update_sale_order", store=True)
    status_transfer = fields.Selection(
        selection=[('new', 'Mới'),
                   ('check', 'Đã check'),
                   ('sent', 'Đang gửi hàng'),
                   ('delivery', 'Đang giao hàng'),
                   ('successful', 'Giao thành công'),
                   ('return', 'Hoàn'),
                   ('cancel', 'Hủy')
                   ], default='new',
        string='Trạng thái vận đơn', compute="_update_sale_order", store=True)

    # x_branch_id = fields.Many2one('vtg.branch', string='Chi nhánh', compute="_update_sale_order", store=True)

    @api.depends('order_id')
    def _update_sale_order(self):
        for s in self:
            s.type_customer = s.order_id.type_customer
            s.status_transfer = s.order_id.status_transfer
            # s.x_branch_id = s.order_id.x_branch_id


class SaleOrderTransfer(models.Model):
    _name = 'sale.order.transfer.history'

    sale_id = fields.Many2one('sale.order', string='Đơn hàng')
    date_order = fields.Datetime(string='Ngày mua hàng', related='sale_id.date_order')
    date = fields.Datetime(string='Ngày cập nhật')
    status_transfer_old = fields.Selection(
        selection=[('new', 'Mới'),
                   ('check', 'Đã check'),
                   ('sent', 'Đang gửi hàng'),
                   ('delivery', 'Đang giao hàng'),
                   ('successful', 'Giao thành công'),
                   ('return', 'Hoàn'),
                   ('cancel', 'Hủy')
                   ], default='new',
        string='Trạng thái vận cũ')
    status_transfer_new = fields.Selection(
        selection=[('new', 'Mới'),
                   ('check', 'Đã check'),
                   ('sent', 'Đang gửi hàng'),
                   ('delivery', 'Đang giao hàng'),
                   ('successful', 'Giao thành công'),
                   ('return', 'Hoàn'),
                   ('cancel', 'Hủy')
                   ], default='new',
        string='Trạng thái vận đơn mới')
