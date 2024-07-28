# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import urllib3
import certifi
from datetime import date, datetime, timedelta


class VTGbranch(models.Model):
    _name = 'vtg.branch'

    name = fields.Char(string='Tên chi nhánh')
    address = fields.Char(string='Địa chỉ')
    user_id = fields.Many2one('res.users', string='Thu ngân')


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    booking_id = fields.Many2one('crm.lead.booking')

    @api.model
    def create(self, vals):
        sale_id = super(SaleOrder, self).create(vals)
        if sale_id.booking_id:
            subject = 'Đặt lịch: ' + sale_id.booking_id.name + ' khách hàng ' + sale_id.booking_id.partner_name + ' Được tạo đơn hàng'
            partner_to = []
            partner_to.append(sale_id.user_id.partner_id.id)
            partner_to.append(sale_id.team_id.user_id.partner_id.id)
            # self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
            #                                                    partner_to,
            #                                                    subject, 'sale.order', self.id,
            #                                                    datetime.now())
        # else:
        #     subject = 'Đơn hàng: ' + sale_id.name + ' khách hàng ' + sale_id.partner_id.name + ' được tạo'
        #     partner_to = []
        #     partner_to.append(sale_id.user_id.partner_id.id)
        #     if sale_id.team_id:
        #         partner_to.append(sale_id.team_id.user_id.partner_id.id)
        #     self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
        #                                                        partner_to,
        #                                                        subject,'sale.order', self.id,
        #                                                        datetime.now())
        return sale_id

    def write(self, vals):
        for sale_id in self:
            status_transfer_old = sale_id.status_transfer
            res = super(SaleOrder, self).write(vals)
            status_transfer_new = sale_id.status_transfer
            if status_transfer_old != status_transfer_new and status_transfer_new == 'successful':
                subject = 'Đơn hàng: ' + sale_id.name + ' khách hàng ' + sale_id.partner_id.name + ' được giao thành công'
                partner_to = []
                partner_to.append(sale_id.user_id.partner_id.id)
                partner_to.append(sale_id.team_id.user_id.partner_id.id)
                # self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
                #                                                    partner_to,
                #                                                    subject, 'sale.order', self.id,
                #                                                    datetime.now())
            return res


class CRM_Booking(models.Model):
    _name = 'crm.lead.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    @api.model
    def _get_default_code(self):
        return self.env["ir.sequence"].next_by_code("crm.lead.booking")

    def _default_team_id(self, user_id):
        domain = []
        return self.env['crm.team']._get_default_team_id(user_id=user_id, domain=domain)

    name = fields.Char(string='Mã đặt lịch', track_visibility='onchange')
    lead_id = fields.Many2one('crm.lead', string='Cơ hội', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Tham chiếu khách hang', track_visibility='onchange')
    partner_name = fields.Char(string='Tên khách hàng', track_visibility='onchange')
    partner_phone = fields.Char(string='SĐT khách hàng', track_visibility='onchange')
    partner_address = fields.Char(string='Địa chỉ khách hàng', track_visibility='onchange')
    branch_id = fields.Many2one('vtg.branch', string='Chi nhánh', track_visibility='onchange')
    category_id = fields.Many2many('product.category', string='Loại dịch vụ', track_visibility='onchange')
    date = fields.Date(string='Ngày khách đặt', track_visibility='onchange', default=fields.Date.today())
    slot_time = fields.Selection([
        ('8h30', '08:30'),
        ('9h00', '09:00'),
        ('9h30', '09:30'),
        ('10h00', '10:00'),
        ('10h30', '10:30'),
        ('11h00', '11:00'),
        ('11h30', '11:30'),
        ('12h00', '12:00'),
        ('12h30', '12:30'),
        ('13h00', '13:00'),
        ('13h30', '13:30'),
        ('14h00', '14:00'),
        ('14h30', '14:30'),
        ('15h00', '15:00'),
        ('15h30', '15:30'),
        ('16h00', '16:00'),
        ('16h30', '16:30'),
        ('17h00', '17:00'),
        ('17h30', '17:30'),
        ('18h00', '18:00'),
        ('18h30', '18:30'),
        ('19h00', '19:00'),
        ('19h30', '19:30'),
        ('20h00', '20:00'),
        ('20h30', '20:30'),
    ], track_visibility='onchange', string='Khung giờ đặt')
    detail_ids = fields.One2many('crm.lead.booking.detail', 'booking_id', string='Sản phẩm quan tâm',
                                 track_visibility='onchange')
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    booking_log_note_ids = fields.One2many('crm.lead.booking.log.note', 'booking_id', string='Ghi chú')
    weekday = fields.Selection([
        ('monday', 'Thứ 2'),
        ('tuesday', 'Thứ 3'),
        ('wednesday', 'Thứ 4'),
        ('thursday', 'Thứ 5'),
        ('friday', 'Thứ 6'),
        ('saturday', 'Thứ 7'),
        ('sunday', 'Chủ nhật'),
    ], string='Thứ', default='monday', track_visibility='onchange', compute="_get_weekday", store=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirm', 'Chờ khách tới'),
        ('confirmed', 'Khách đã tới'),
        ('cancel_buy', 'Khách đã tới nhưng không mua'),
        ('cancel', 'Từ chối'),
        ('cancel_10', 'Hủy quá 10 ngày')
    ], string='Trạng thái', default='draft', track_visibility='onchange')
    date_sent = fields.Datetime(string="Ngày gửi salon")
    team_id = fields.Many2one('crm.team', string='Nhóm khinh doanh',
                              default=lambda self: self._default_team_id(self.env.uid),
                              index=True, tracking=True,
                              help='When sending mails, the default email address is taken from the Sales Team.')
    user_id = fields.Many2one('res.users', string='Nhân viên kinh doanh', index=True, tracking=True,
                              default=lambda self: self.env.user)
    date_start = fields.Datetime(string='Thời gian bắt đầu')
    date_end = fields.Datetime(string='Thời gian kết thúc')
    sale_ids = fields.One2many('sale.order', 'booking_id', string='Đơn hàng')
    status_customer = fields.Selection(
        [('not_yet', 'Khách chưa tới'), ('yet', 'Khách tới'), ('wait', 'Chờ khách tới'), ('buy', 'Khách đã mua')],
        string="Trạng thái khách tới",
        compute="_compute_status_customer", store=False)
    state_id = fields.Many2one('res.country.state', string='Tỉnh/Thành phố', domain=[('country_id', '=', 241)])
    source_id = fields.Many2one('utm.source', 'Nguồn', ondelete='cascade')
    arrival_date = fields.Datetime(string='Ngày khách tới')
    type_customer = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', default='new', compute="auto_update_type_customer", store=True)
    create_lead = fields.Datetime(string='Ngày tạo lead', compute="_get_marketing_sale", store=True)
    date_open_lead = fields.Datetime(string='Ngày giao lead', compute="_get_marketing_sale", store=True)
    marketing_id = fields.Many2one('res.users', string='Marketing', compute="_get_marketing_sale", store=True)

    sale_order_count = fields.Integer('Sale Order Count', compute="_compute_sale_order")

    def _compute_sale_order(self):
        for item in self:
            item.sale_order_count = self.env['sale.order'].search_count([('booking_id', '=', item.id)])

    def action_view_sale_order(self):
        action = self.env.ref('sale.action_orders').read()[0]
        if action.get('domain', ''):
            action['domain'] = str(eval(action['domain']) + [('booking_id', '=', self.id)])
        return action

    @api.depends('lead_id')
    def _get_marketing_sale(self):
        for s in self:
            if s.lead_id:
                s.marketing_id = s.lead_id.marketing_id
                s.create_lead = s.lead_id.create_date
                s.date_open_lead = s.lead_id.date_open
            else:
                s.marketing_id = s.user_id
                s.date_open_lead = s.date_sent
                s.create_lead = s.date_sent

    def vtg_crm_lead_booking_log_note_action_new(self):
        view_id = self.env.ref('vtg_custom_lead.vtg_crm_lead_booking_log_note_form_view').id
        ctx = dict(
            default_booking_id=self.id,
            default_state=self.state,
        )
        return {
            'name': _('Ghi chú'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.lead.booking.log.note',
            'view_id': view_id,
            'target': 'new',
            'context': ctx,
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }

    @api.depends('lead_id')
    def auto_update_type_customer(self):
        for s in self:
            if s.lead_id:
                s.type_customer = s.lead_id.type_customer
            else:
                s.type_customer = 'new'

    @api.depends('date')
    def _get_weekday(self):
        for s in self:
            wd = date.weekday(s.date)
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            s.weekday = days[wd]

    @api.depends('state')
    def _compute_status_customer(self):
        for s in self:
            if s.state == 'confirm':
                if s.date_end < datetime.now():
                    s.status_customer = 'not_yet'
                else:
                    s.status_customer = 'wait'
            elif s.state == 'confirmed' and len(s.sale_ids) > 0:
                s.status_customer = 'buy'
            else:
                s.status_customer = ''

    def action_auto_10_day(self):
        date_10 = datetime.now() - timedelta(days=10)
        booking_ids = self.env['crm.lead.booking'].search(
            [('date_sent', '<', date_10), ('state', '=', 'confirm')])
        for booking_id in booking_ids:
            booking_id.state = 'cancel_10'
            # subject = 'Khách hàng: ' + str(booking_id.partner_id.name) + ' SĐT ' + str(
            #     booking_id.partner_phone) + 'Quá 10 ngày không tới salon'
            # body = _("""
            #                                Xin chào """ + str(booking_id.user_id.name) + """,
            #
            #                                Đã quá 10 ngày Khách hàng chưa tới salon với thông tin đặt lịch sau:
            #                                    Mã đặt lịch: """ + str(booking_id.name) + """
            #                                    Khách hàng: """ + str(booking_id.partner_name) + """
            #                                    Số điện thoại: """ + str(booking_id.partner_phone) + """
            #                                    Ngày đặt: """ + str(booking_id.date) + """
            #                                    Khung giờ đặt: """ + str(booking_id.slot_time) + """
            #
            #                                Chi tiết vui lòng truy cập: https://crm.hermanoss.com/web#id=""" + str(
            #     booking_id.id) + """&cids=1&menu_id=133&action=485&model=crm.lead.booking&view_type=form
            #
            #                                Thanks and best regards,
            #                    """)
            # email = self.env['ir.mail_server'].build_email(
            #     email_from=self.env.user.email,
            #     email_to=booking_id.user_id.login,
            #     subject=subject, body=body
            # )
            # self.env['ir.mail_server'].send_email(email)
        # partner_to = []
        # partner_to.append(booking_id.user_id.partner_id.id)
        # self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
        #                                                    partner_to,
        #                                                    subject, 'crm.lead.booking', self.id,
        #                                                    datetime.now())

    def action_auto(self):
        date_5 = datetime.now() - timedelta(minutes=30)
        booking_ids = self.env['crm.lead.booking'].search(
            [('date_end', '>', date_5), ('date_end', '<=', datetime.now()), ('state', '=', 'confirm')])
        for booking_id in booking_ids:
            subject = 'Khách hàng: ' + str(booking_id.partner_id.name) + ' SĐT ' + str(
                booking_id.partner_phone) + 'chưa tới salon'
            body = _("""
                               Xin chào salon """ + str(booking_id.user_id.name) + """,

                               Khách hàng chưa tới salon với thông tin đặt lịch sau:
                                   Mã đặt lịch: """ + str(booking_id.name) + """
                                   Khách hàng: """ + str(booking_id.partner_name) + """
                                   Số điện thoại: """ + str(booking_id.partner_phone) + """
                                   Ngày đặt: """ + str(booking_id.date) + """
                                   Khung giờ đặt: """ + str(booking_id.slot_time) + """

                               Chi tiết vui lòng truy cập: https://crm.hermanoss.com/web#id=""" + str(booking_id.id) + """&cids=1&menu_id=133&action=485&model=crm.lead.booking&view_type=form

                               Thanks and best regards,
                   """)
            email = self.env['ir.mail_server'].build_email(
                email_from=self.env.user.email,
                email_to=booking_id.user_id.login,
                subject=subject, body=body
            )
            # self.env['ir.mail_server'].send_email(email)

    @api.onchange('slot_time', 'date')
    def onchange_compute_date(self):
        if not self.slot_time or not self.date:
            return
        start_hour = self.slot_time.split('h')[0]
        start_minute = self.slot_time.split('h')[1]
        today_with_time = datetime(
            year=self.date.year,
            month=self.date.month,
            day=self.date.day,
        )
        self.date_start = today_with_time + timedelta(hours=int(start_hour) - 7) + timedelta(minutes=int(start_minute))
        self.date_end = today_with_time + timedelta(hours=int(start_hour) - 7) + timedelta(
            minutes=int(start_minute) + 30)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('crm.lead.booking') or '/'
        # booking_ids = self.env['crm.lead.booking'].sudo().search(
        #     [('user_id', '!=', vals['user_id']), ('state', '=', 'confirm'),
        #      ('partner_phone', '=', vals['partner_phone'])])
        # if booking_ids:
        #     raise UserError('Khách đã có lịch đang chờ khách tới')
        booking = super(CRM_Booking, self).create(vals)
        return booking

    def action_send_booking(self):
        users_ids = self.env['res.users'].search([('x_branch_id', '=', self.branch_id.id)])
        emails_to = ''
        partner_to = []
        if self.branch_id.id in (8, 9):
            emails_to = 'nhungnt.hermanoss@gmail.com'
            partner_to.append(18712)
        else:
            for users_id in users_ids:
                emails_to += users_id.login + ','
                partner_to.append(users_id.partner_id.id)
        subject = 'Salon của bạn có đặt lịch: ' + self.name + ' khách hàng ' + self.partner_name
        body = _("""
                    Xin chào salon """ + self.branch_id.name + """,
                    
                    Salon có lịch đặt hẹn sau:
                        Mã đặt lịch: """ + self.name + """
                        Khách hàng: """ + self.partner_name + """
                        Số điện thoại: """ + self.partner_phone + """
                        Ngày đặt: """ + str(self.date) + """
                        Khung giờ đặt: """ + self.slot_time + """
                        
                    Chi tiết vui lòng truy cập: https://crm.hermanoss.com/web#id=""" + str(self.id) + """&cids=1&menu_id=133&action=485&model=crm.lead.booking&view_type=form
                         
                    Thanks and best regards,
        """)
        email = self.env['ir.mail_server'].build_email(
            email_from=self.env.user.email,
            email_to=emails_to,
            subject=subject, body=body
        )
        # self.env['ir.mail_server'].send_email(email)
        self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
                                                           partner_to,
                                                           subject, 'crm.lead.booking', self.id,
                                                           datetime.now())

        self.state = 'confirm'
        self.date_sent = datetime.now()
        if not self.lead_id:
            lead_id = self.env['crm.lead'].sudo().search(
                [('phone', '=', self.partner_phone), ('user_id', '=', self.user_id.id)], limit=1)
            if not lead_id:
                lead_id = self.env['crm.lead'].create({
                    'name': self.partner_name,
                    'contact_name': self.partner_name,
                    'phone': self.partner_phone,
                    'source_id': self.source_id.id,
                    'user_id': self.user_id.id,
                    'marketing_id': self.user_id.id,
                    'team_id': self.team_id.id,
                    'company_id': 1,
                    'type': 'opportunity',
                    'stage_id': 9,
                    'date_open': datetime.now(),
                    'date_input': datetime.today(),
                    'partner_id': self.partner_id.id,
                    'street': self.partner_address,
                    'state_id': self.state_id.id,
                })
            self.lead_id = lead_id

    def action_confirm_booking(self):
        self.state = 'confirmed'
        self.arrival_date = datetime.now()

    def action_cancel_booking(self):
        self.state = 'cancel'

    def action_cancel_buy(self):
        self.state = 'cancel_buy'

    def action_create_order(self):
        if not self.partner_id:
            return self.env.ref("sale_crm.crm_quotation_partner_action").read()[0]
        else:
            return self.action_new_quotation()

    def action_new_quotation(self):
        action = self.env.ref("sale_crm.sale_action_quotations_new").read()[0]
        action['context'] = {
            'search_default_opportunity_id': self.lead_id.id,
            'default_opportunity_id': self.lead_id.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.lead_id.team_id.id,
            'default_booking_id': self.id,
            'default_user_id': self.user_id.id,
            'default_source_id': self.source_id.id,
            'default_x_branch_id': self.branch_id.id,
        }
        return action

    @api.onchange('lead_id')
    def onchange_lead(self):
        if self.lead_id:
            self.partner_id = self.lead_id.partner_id
            self.partner_name = self.lead_id.contact_name
            self.partner_phone = self.lead_id.phone
            self.partner_address = self.lead_id.street
            self.state_id = self.lead_id.state_id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_name = self.partner_id.name
            self.partner_phone = self.partner_id.phone
            self.partner_address = self.partner_id.street
            self.state_id = self.partner_id.state_id
            # lead_ids = self.env['crm.lead'].sudo().search(
            #     [('phone', '=', self.partner_id.phone)])
            # for lead_id in lead_ids:
            #     self.source_id = lead_id.source_id

    def notification(self):
        self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
                                                           [3],
                                                           f'Bạn có một booking mới',
                                                           'crm.lead.booking', self.id,
                                                           datetime.now())


class CRMBookingLogNote(models.Model):
    _name = 'crm.lead.booking.log.note'

    booking_id = fields.Many2one('crm.lead.booking', string='Booking')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirm', 'Chờ khách tới'),
        ('confirmed', 'Khách đã tới'),
        ('cancel_buy', 'Khách đã tới nhưng không mua'),
        ('cancel', 'Từ chối'),
        ('cancel_10', 'Hủy quá 10 ngày')
    ], string='Trạng thái', default='draft', track_visibility='onchange')
    note = fields.Char('Ghi chú')
    content = fields.Selection([('pre_sale', 'Tư vấn trước bán'), ('after_sale', 'Chăm sóc sau bán')],
                               string="Nội dung liên hệ",
                               default='pre_sale')
    contact_form = fields.Selection(
        [('video', 'Video Call'),
         ('tele_sale', 'Tele sale'),
         ('chat', 'Chat'),
         ('meeting', 'Gặp mặt'),
         ('survey', 'Gửi khảo sát'),
         ('other', 'Khác')],
        string="Hình thức liên hệ",
        default='tele_sale')
    result = fields.Selection(
        [('interacted', 'Đã tương tác'),
         ('no_answer', 'Không trả lời'),
         ('call_back', 'Gọi lại sau'),
         ('cancel_meeting', 'Hủy gặp'),
         ('send_survey', 'Đã gửi khảo sát'),
         ('answer_survey', 'Đã trả lời khảo sát'),
         ('other', 'Khác')],
        string="Kết quả",
        default='interacted')


class CRMBookingDetail(models.Model):
    _name = 'crm.lead.booking.detail'

    booking_id = fields.Many2one('crm.lead.booking')
    product_id = fields.Many2one('product.product', string='Sản phẩm quan tâm')
    qty = fields.Integer(string='Số lượng')
