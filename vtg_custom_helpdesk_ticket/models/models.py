# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError

_logger = logging.getLogger(__name__)


class HelpdeskStatusCustomer(models.Model):
    _name = "helpdesk.ticket.status.customer"

    name = fields.Char('Trạng thái sử dụng')


class HelpdeskRatingCustomersale(models.Model):
    _name = "helpdesk.ticket.rating.sale.reason"

    name = fields.Char('Tiêu chí đánh giá')
    rating_sales = fields.Selection(selection=[
        ('1', 'Rất tệ'),
        ('2', 'Tệ'),
        ('3', 'Tạm được'),
        ('4', 'Tốt'),
        ('5', 'Tuyệt vời'),
    ], string='Đánh giá chất lượng Sales', default="1")


class HelpdeskRatingCustomer(models.Model):
    _name = "helpdesk.ticket.rating.reason"

    name = fields.Char('Tiêu chí đánh giá')
    rating_customer = fields.Selection(selection=[
        ('1', 'Rất tệ'),
        ('2', 'Tệ'),
        ('3', 'Tạm được'),
        ('4', 'Tốt'),
        ('5', 'Tuyệt vời'),
    ], string='Đánh giá khách hàng', default="1")


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    sale_id = fields.Many2one('sale.order', string='Đơn hàng')
    source_id = fields.Many2one('utm.source', string='Nguồn')
    type_care = fields.Selection(selection=[('3', '1-3 Ngày'), ('30', '30 Ngày'), ('180', '180 Ngày')],
                                 string='Hình thức chăm sóc', default="3")
    status_customer = fields.Many2one('helpdesk.ticket.status.customer', string='Trạng thái sử dụng khách hàng')
    rating_customer = fields.Selection(selection=[
        ('0', 'All'),
        ('1', 'Rất tệ'),
        ('2', 'Tệ'),
        ('3', 'Tạm được'),
        ('4', 'Tốt'),
        ('5', 'Tuyệt vời'),
    ],
        string='Đánh giá khách hàng', default="0")
    rating_main_employee = fields.Selection(selection=[
        ('0', 'All'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
    ],
        string='Thợ chính', default="0")
    rating_salon = fields.Selection(selection=[
        ('0', 'All'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
    ],
        string='Salon', default="0")
    rating_product = fields.Selection(selection=[
        ('0', 'All'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
    ],
        string='Product', default="0")
    rating_reason_ids = fields.Many2many('helpdesk.ticket.rating.reason', string="Lý do đánh giá",
                                         domain="[('rating_customer', '=', rating_customer)]")

    rating_sales = fields.Selection(selection=[
        ('0', 'All'),
        ('1', 'Rất tệ'),
        ('2', 'Tệ'),
        ('3', 'Tạm được'),
        ('4', 'Tốt'),
        ('5', 'Tuyệt vời'),
    ],
        string='Đánh giá khách hàng', default="0")
    rating_sale_reason_ids = fields.Many2many('helpdesk.ticket.rating.sale.reason', string="Lý do đánh giá",
                                              domain="[('rating_sales', '=', rating_sales)]")

    type_customer_order = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', related='sale_id.type_customer')
    date_order = fields.Datetime(string='Ngày đơn hàng', related='sale_id.date_order', store=True)
    x_branch_order_id = fields.Many2one('vtg.branch', string='Chi nhánh', related='sale_id.x_branch_id')
    x_user_order_id = fields.Many2one('res.users', string='Nhân viên kinh doanh', related='sale_id.user_id')
    master_employee_order_id = fields.Many2one('hr.employee', string='Thợ chính', related='sale_id.master_employee_id')
    # amount_order_total = fields.Monetary(string='Tổng', related='sale_id.amount_total')
    amount_pay = fields.Float(string="Đã thanh toán", related='sale_id.amount_pay')
    lead_log_note_ids = fields.One2many('helpdesk.ticket.log.note', 'ticket_id', string='Ghi chú')
    user_sale_id = fields.Many2one('res.users', string='Nhân viên kinh doanh', compute="_get_sale_user", store=True)

    @api.depends('sale_id')
    def _get_sale_user(self):
        for s in self:
            s.user_sale_id = s.sale_id.user_id

    def write(self, vals):
        for ticket_id in self:
            stage_id_old = ticket_id.stage_id.id
            stage_old = ticket_id.stage_id
            res = super(HelpdeskTicket, self).write(vals)
            stage_id_new = ticket_id.stage_id.id
            stage_new = ticket_id.stage_id
            if stage_id_old != stage_id_new and stage_old.sequence < stage_new.sequence:
                note = ticket_id.check_lead_log_note_action(ticket_id, stage_old)
                if not note:
                    raise UserError("Bạn vui lòng cập nhật ghi chú trước khi chuyển trạng thái")

            return res

    def check_lead_log_note_action(self, lead_id, stage_id):
        note = self.env['helpdesk.ticket.log.note'].search(
            [('ticket_id', '=', lead_id.id), ('stage_id', '=', stage_id.id)])
        return note

    def vtg_crm_lead_log_note_action_new(self):
        view_id = self.env.ref('vtg_custom_helpdesk_ticket.vtg_helpdesk_ticket_log_note_form_view').id
        ctx = dict(
            default_ticket_id=self.id,
            default_stage_id=self.stage_id.id,
        )
        return {
            'name': _('Ghi chú'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'helpdesk.ticket.log.note',
            'view_id': view_id,
            'target': 'new',
            'context': ctx,
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }

    def vtg_helpdesk_refund_action_new(self):
        view_id = self.env.ref('sale.view_order_form').id
        ctx = dict(
            default_ticket_id=self.id,
            default_partner_id=self.partner_id.id,
            default_source_id=self.source_id.id,
        )
        return {
            'name': _('Đơn hàng'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'view_id': view_id,
            'target': 'new',
            'context': ctx,
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }


class HelpdeskTicketConvert2Lead(models.TransientModel):
    _inherit = "helpdesk.ticket.to.lead"
    _description = "Convert Ticket to Lead"

    def action_convert_to_lead(self):
        self.ensure_one()
        # create partner if needed
        if self.action == 'create':
            self.partner_id = self.ticket_id._find_matching_partner(force_create=True).id

        lead_sudo = self.env['crm.lead'].with_context(
            mail_create_nosubscribe=True,
            mail_create_nolog=True
        ).sudo().create({
            'name': self.partner_id.name,
            'partner_id': self.partner_id.id,
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
            'department_id': self.team_id.user_id.employee_id.department_id.id,
            'description': self.ticket_id.description,
            'ticket_id': self.ticket_id.id,
            'source_id': self.ticket_id.source_id.id,
            'email_cc': self.ticket_id.email_cc,
            'phone': self.partner_id.phone,
            'type_lead': 'resale',
            'contact_name': self.partner_id.name,
            'street': self.partner_id.street,
        })
        lead_sudo.message_post_with_view(
            'mail.message_origin_link', values={'self': lead_sudo, 'origin': self.ticket_id},
            subtype_id=self.env.ref('mail.mt_note').id, author_id=self.env.user.partner_id.id
        )

        # move the mail thread and attachments
        self.ticket_id.message_change_thread(lead_sudo)
        attachments = self.env['ir.attachment'].search(
            [('res_model', '=', 'helpdesk.ticket'), ('res_id', '=', self.ticket_id.id)])
        attachments.sudo().write({'res_model': 'crm.lead', 'res_id': lead_sudo.id})
        # self.ticket_id.action_archive()

        # return to lead (if can see) or ticket (if cannot)
        try:
            self.env['crm.lead'].check_access_rights('read')
            self.env['crm.lead'].browse(lead_sudo.ids).check_access_rule('read')
        except:
            return {
                'name': _('Ticket Converted'),
                'view_mode': 'form',
                'res_model': self.ticket_id._name,
                'type': 'ir.actions.act_window',
                'res_id': self.ticket_id.id
            }

        # return the action to go to the form view of the new Ticket
        action = self.sudo().env.ref('crm.crm_lead_all_leads').read()[0]
        action.update({
            'res_id': lead_sudo.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
        })
        return action


class HelpdeskLOGNOTE(models.Model):
    _name = 'helpdesk.ticket.log.note'

    ticket_id = fields.Many2one('helpdesk.ticket', string='CSKH')
    stage_id = fields.Many2one('helpdesk.stage', string="Trạng thái")
    note = fields.Char('Ghi chú')
    content = fields.Selection([('ask_about', 'Hỏi thăm tình trạng sử dụng tóc'),
                                ('share_document', 'Chia sẻ và gửi hướng dẫn sử dụng'),
                                ('feedback', 'Xin feedback và đánh giá'),
                                ('remind', 'Nhắc nhở sử dụng voucher và tới salon chăm sóc'),
                                ('introduce', 'Xin lời giới thiệu'),
                                ('event', 'Mời tham gia các xử kiện cộng đồng'),
                                ],
                               string="Nội dung liên hệ",
                               default='ask_about')
    contact_form = fields.Selection(
        [('video', 'Video Call'),
         ('tele_sale', 'Tele sale'),
         ('chat', 'Chat'),
         ('other', 'Khác')],
        string="Hình thức liên hệ",
        default='tele_sale')
    result = fields.Selection(
        [('interacted', 'Đã tương tác'),
         ('no_answer', 'Không trả lời'),
         ('call_back', 'Gọi lại sau'),
         ('other', 'Khác')],
        string="Kết quả",
        default='interacted')

    @api.model
    def create(self, vals):
        note = super(HelpdeskLOGNOTE, self).create(vals)

        content = dict(self._fields['content'].selection).get(self.content)
        result = dict(self._fields['result'].selection).get(self.result)
        contact_form = dict(self._fields['contact_form'].selection).get(self.contact_form)

        # content = ''
        # if note.content == 'pre_sale':
        #     content = 'Tư vấn trước bán'
        # elif note.content == 'after_sale':
        #     content = 'Chăm sóc sau bán'
        #
        # contact_form = ''
        # if note.contact_form == 'video':
        #     contact_form = 'Video Call'
        # elif note.contact_form == 'tele_sale':
        #     contact_form = 'Tele sale'
        # elif note.contact_form == 'chat':
        #     contact_form = 'Chat'
        # elif note.contact_form == 'meeting':
        #     contact_form = 'Gặp mặt'
        # elif note.contact_form == 'other':
        #     contact_form = 'Khác'
        #
        # result = ''
        # if note.result == 'interacted':
        #     result = 'Đã tương tác'
        # elif note.result == 'no_answer':
        #     result = 'Không trả lời'
        # elif note.result == 'call_back':
        #     result = 'Gọi lại sau'
        # elif note.result == 'cancel_meeting':
        #     result = 'Hủy gặp'
        # elif note.result == 'other':
        #     result = 'Khác'

        chatter_message = _('''<b> Nội dung liên hệ: </b> %s <br/>
                               <b> Hình thức liên hệ: </b> %s <br/>
                               <b> Kết quả: </b> %s <br/>
                               <b> Ghi chú: </b> %s <br/>
                               <b> Trạng thái Note: </b> %s <br/>

                                     ''') % (
            content,
            contact_form,
            result,
            note.note,
            note.stage_id.name,
        )

        note.ticket_id.message_post(body=chatter_message)

        return note
