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

# import phonenumbers
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)


# def validate_phone(phone):
#     try:
#         phone = phonenumbers.parse(phone, 'None')
#     except:
#         phone = phonenumbers.parse(phone, 'VN')
#     if phonenumbers.is_valid_number(phone):
#         return True
#     return False


class CRMLEAD(models.Model):
    _inherit = 'crm.lead'

    date_input = fields.Date(string='Ngày nhập')
    status_text = fields.Text(string='Tình trạng chi tiết')
    status_selection = fields.Selection(
        [('high_forehead', 'Trán cao'),
         ('bald_peak', 'Hói đỉnh'),
         ('thinning_hair', 'Tóc thưa'),
         ('whole_head', 'Rụng Cả Đầu'),
         ('other', 'Không xác định')
         ], string="Tình trạng")
    demand = fields.Text(string='Nhu cầu chi tiết')
    demand_selection = fields.Selection(
        [('directly', 'Đến trực tiếp'), ('at_home', 'Làm tại nhà'), ('online', 'Mua Online')],
        string="Nhu cầu")
    marketing_id = fields.Many2one(
        'res.users', string='Marketing phụ trách', default=lambda self: self.env.user,
        check_company=True, index=True, tracking=True)
    phone = fields.Char(
        'Phone', tracking=50,
        compute='_compute_phone', inverse='_inverse_phone', readonly=False, store=True, required=True)
    booking_ids = fields.One2many('crm.lead.booking', 'lead_id', string='Booking')
    log_call_ids = fields.One2many('crm.lead.log.call', 'lead_id', string='Log Call')
    is_exist = fields.Boolean(string='Tồn tại lead đã có', default=False, compute="_compute_is_exist")
    is_exist1 = fields.Boolean(string='Tồn tại lead đã có', default=False, compute="_compute_is_exist", store=True)
    lead_exist_ids = fields.One2many('crm.lead.exist', 'lead_id', string='Lead tồn tại')
    lead_log_note_ids = fields.One2many('crm.lead.log.note', 'lead_id', string='Ghi chú')
    lead_log_recall_ids = fields.One2many('crm.lead.history.recall', 'lead_id', string='Lịch sử thu hồi')
    user_id = fields.Many2one(
        'res.users', string='Salesperson', default=None,
        domain="['&', ('share', '=', False), ('company_ids', 'in', user_company_ids)]",
        check_company=True, index=True, tracking=True)
    status_date_open = fields.Selection(
        [('within_term', 'Trong hạn 2h'), ('overdue', 'Quá hạn 2h'), ('warning', 'Cảnh báo')], string="Trạng thái 2h",
        default='within_term', compute="_compute_status_date_open", store=True)
    send_email = fields.Char(default="none")
    is_recall = fields.Boolean(default=False, string="Thu hồi")
    is_recall_log_note = fields.Boolean(default=False, string="Thu hồi không cập nhập log")
    is_recall_buy = fields.Boolean(default=False, string="Thu hồi 30 ngày chưa mua")
    state_id = fields.Many2one(
        "res.country.state", string='Tỉnh',
        compute='_compute_partner_address_values', readonly=False, store=True,
        domain="[('country_id', '=', 241)]")
    is_resale = fields.Boolean(string='Khách đã mua hàng', default=False)
    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket')
    type_customer = fields.Selection(
        selection=[('new', 'Khách hàng mới'),
                   ('old', 'Khách hàng cũ'),
                   ('find', 'Khách hàng tự tìm')
                   ],
        string='Loại khách hàng', default='new', compute="auto_update_type_customer", store=True)
    date_buy = fields.Datetime(string='Ngày mua hàng ngần nhất', compute="_get_date_order", store=True)

    @api.depends('order_ids')
    def _get_date_order(self):
        for s in self:
            if s.order_ids:
                order_id = self.env['sale.order'].sudo().search([('opportunity_id','=',s.id),('state','in',('sale','done'))],limit=1, order='date_order desc')
                if order_id:
                    s.date_buy = order_id.date_order
                else:
                    s.date_buy = None
            else:
                s.date_buy = None

    @api.depends('phone')
    def auto_update_type_customer(self):
        for s in self:
            if s.phone:
                partner_ids = self.env['res.partner'].sudo().search(
                    [('phone', '=', s.phone)])
                if partner_ids:
                    type_customer = 'new'
                    for partner_id in partner_ids:
                        order_ids = self.env['sale.order'].sudo().search(
                            [('partner_id', '=', partner_id.id),
                             ('date_order', '<', s.create_date),
                             ('state', 'in', ('sale', 'done'))])
                        a = 0
                        for order_id in order_ids:
                            for line in order_id.order_line:
                                if line.product_id.categ_id.id == 1:
                                    a = 1
                        if a == 1:
                            type_customer = 'old'
                        else:
                            type_customer = 'new'
                    s.type_customer = type_customer
                elif s.marketing_id.id == s.user_id.id:
                    s.type_customer = 'find'
                else:
                    s.type_customer = 'new'
            else:
                s.type_customer = 'new'

    @api.depends('date_open')
    def _compute_status_date_open(self):
        for s in self:
            if s.date_open:
                date_2h = s.date_open + timedelta(hours=2)
                date_15ph = s.date_open + timedelta(hours=2) - timedelta(minutes=15)
                if s.stage_id.id == 1:
                    if date_15ph >= datetime.now():
                        s.status_date_open = 'within_term'
                    elif date_15ph < datetime.now() and datetime.now() < date_2h:
                        s.status_date_open = 'warning'
                    elif date_2h < datetime.now():
                        s.status_date_open = 'overdue'
            else:
                s.status_date_open = False

    def action_auto_update_log_note(self):
        lead_2h_ids = self.env['crm.lead'].search(
            [('stage_id', '=', 1), ('lead_log_note_ids', '=', []), ('type', '=', 'opportunity'),
             ('date_open', '>', datetime.now() - timedelta(hours=2))])
        for lead_id in lead_2h_ids:
            lead_id.type = 'lead'
            lead_id.user_id = None
            lead_id.team_id = None
            self.env['crm.lead.history.recall'].create({
                'user_id': lead_id.user_id.id,
                'team_id': lead_id.team_id.id,
                'reason': 'Thu hồi trong 2 tiếng không cập nhật ghi chú ở trạng thái mới',
                'date_time': datetime.now(),
                'lead_id': lead_id.id
            })
        query = """
            SELECT * FROM (
            SELECT "max"(b.create_date) as create_date, a.id 
            FROM crm_lead a 
            JOIN crm_lead_log_note b on a.id = b.lead_id
            WHERE a.stage_id not in (1, 16, 11, 9, 17, 13) and a.type = 'opportunity'
            GROUP BY a.id) as a 
            WHERE create_date <  now() - INTERVAL '7 days'
        """
        self._cr.execute(query, ())
        res = self._cr.fetchall()
        for r in res:
            lead_id = self.env['crm.lead'].search(
                [('id', '=', r[1])])
            lead_id.is_recall_log_note = True
            self.env['crm.lead.history.recall'].create({
                'user_id': lead_id.user_id.id,
                'team_id': lead_id.team_id.id,
                'reason': 'Thu hồi trong 7 Ngày không cập nhật ghi chú ở trạng thái' + lead_id.stage_id.name,
                'date_time': datetime.now(),
                'lead_id': lead_id.id
            })

        query_30 = """
                SELECT a.id 
                FROM crm_lead a 
                WHERE a.stage_id not in (16, 11, 17, 13) 
                and a.type = 'opportunity'
                AND date_open > now() - INTERVAL '30 days'
                """
        self._cr.execute(query_30, ())
        res_30 = self._cr.fetchall()
        for r in res_30:
            lead_id = self.env['crm.lead'].search(
                [('id', '=', r[0])])
            lead_id.is_recall_buy = True
            self.env['crm.lead.history.recall'].create({
                'user_id': lead_id.user_id.id,
                'team_id': lead_id.team_id.id,
                'reason': 'Thu hồi trong 30 ngày không phát sinh đơn hàng từ trạng thái' + lead_id.stage_id.name,
                'date_time': datetime.now(),
                'lead_id': lead_id.id
            })

    def action_auto_2h_update(self):
        # SEND EMAIL USER
        lead_warning_ids = self.env['crm.lead'].search(
            [('status_date_open', '=', 'warning'), ('stage_id', '=', 1), ('send_email', '=', 'none')])
        for lead_id in lead_warning_ids:
            subject = '[CẢNH BÁO 2h] Khách hàng: ' + str(lead_id.name) + ' SĐT ' + str(
                lead_id.phone) + 'Sắp quá hạn gọi 2h'
            body = _("""
                               Xin chào  """ + str(lead_id.user_id.name) + """,

                               Khách hàng thông tin sau:
                                   Khách hàng: """ + str(lead_id.contact_name) + """
                                   Số điện thoại: """ + str(lead_id.phone) + """
                               Sắp quá hạn gọi
                               Chi tiết vui lòng truy cập: https://crm.hermanoss.com/web#id=""" + str(lead_id.id) + """&menu_id=133&cids=1&action=192&model=crm.lead&view_type=form

                               Thanks and best regards,
                   """)
            email = self.env['ir.mail_server'].build_email(
                email_from=self.env.user.email,
                email_to=lead_id.user_id.login,
                subject=subject, body=body
            )
            lead_id.send_email = "send_user"
            # self.env['ir.mail_server'].send_email(email)
        # SEND EMAIL LEAD
        lead_overdue_ids = self.env['crm.lead'].search(
            [('status_date_open', '=', 'overdue'), ('stage_id', '=', 1), ('send_email', '!=', 'send_lead')])
        for lead_id in lead_overdue_ids:
            subject = '[QUÁ HẠN 2h] Khách hàng: ' + str(lead_id.name) + ' SĐT ' + str(
                lead_id.phone) + 'đã quá thời gian gọi 2h'
            body = _("""
                               Xin chào """ + str(lead_id.team_id.user_id.name) + """,

                               Khách hàng thông tin sau:
                                   Khách hàng: """ + str(lead_id.contact_name) + """
                                   Số điện thoại: """ + str(lead_id.phone) + """
                                   Đang được chăm sóc bởi: """ + str(lead_id.user_id.name) + """
                               Đã quá hạn gọi 2h
                               Chi tiết vui lòng truy cập: https://crm.hermanoss.com/web#id=""" + str(lead_id.id) + """&menu_id=133&cids=1&action=192&model=crm.lead&view_type=form

                               Thanks and best regards,
                   """)
            email = self.env['ir.mail_server'].build_email(
                email_from=self.env.user.email,
                email_to=lead_id.team_id.user_id.login,
                subject=subject, body=body
            )
            lead_id.send_email = "send_lead"
            # self.env['ir.mail_server'].send_email(email)

    def _compute_is_exist(self):
        for s in self:
            if s.phone:
                lead_exist_ids = self.env['crm.lead'].sudo().search(
                    [('active', '=', True), ('phone', '=', s.phone), ('id', '!=', s.id)])
                if lead_exist_ids:
                    s.is_exist = True
                    s.is_exist1 = True
                else:
                    s.is_exist = False
                    s.is_exist1 = False
            else:
                s.is_exist = False
                s.is_exist1 = False

    # @api.onchange('phone')
    # def _onchange_phone_validation(self):
    #     if self.phone:
    #         query = """
    #                 SELECT a.id, a.name,c.name user_name, d.name team_name
    #                 FROM crm_lead a
    #                 LEFT JOIN res_users b on a.user_id = b.id
    #                 LEFT JOIN res_partner c on b.partner_id = c.id
    #                 LEFT JOIN crm_team d on a.team_id = d.id
    #                 WHERE a.phone = %s
    #                 AND a.stage_id in (SELECT id FROM crm_stage WHERE is_won != TRUE)
    #             """
    #         self.env.cr.execute(query, (str(self.phone),))
    #         res = self.env.cr.fetchall()
    #         team_name = ''
    #         if res:
    #             for r in res:
    #                 if r[3]:
    #                     team_name = r[3]
    #             message = _('Số điện thoại bị trùng đang chăm sóc bởi nhóm: ' + team_name)
    #             raise UserError(message)
    #         if not validate_phone(self.phone):
    #             message = ''
    #             message += f'- Số điện thoại: {self.phone} không phải là số Việt Nam\n'
    #             if message:
    #                 raise UserError(message)
    #
    #     else:
    #         message = _("Lead Bắt buộc phải có số điện thoại")
    #         raise UserError(message)

    def action_sent_resale(self):
        self.type_lead = 'resale'
        self.team_id = 12

    @api.model
    def create(self, vals):
        if vals.get('phone'):
            que = """
                SELECT * FROM sale_order a 
                JOIN res_partner b on a.partner_id = b.id
                WHERE b.phone = %s
            """
            self.env.cr.execute(que, (str(vals.get('phone')),))
            res_resale = self.env.cr.fetchall()
            if res_resale:
                vals.update({
                    'is_resale': True
                })

                # view = self.env.ref('sh_message.sh_message_wizard')
                # view_id = view and view.id or False
                # context = dict(self._context or {})
                # context['message'] = 'Lead của bạn đã mua hàng trước đó, Vậy lead sẽ được chuyển sang Re-Sale chăm sóc'
                # return {
                #     'name': 'Lead đã mua hàng',
                #     'type': 'ir.action.act_window',
                #     'view_type': 'form',
                #     'view_mode': 'form',
                #     'res_model': 'sh.message.wizard',
                #     'views': [(view.id, 'form')],
                #     'view_id': view.id,
                #     'target': 'new',
                #     'context': context
                # }
                # title = _("Khách đã mua!")
                # message = _("Khách hàng đã mua hàng từ trước, Lead sẽ được chuyển sang Re-sale chăm sóc!")
                # return {
                #     'type': 'ir.actions.client',
                #     'tag': 'display_notification',
                #     'params': {
                #         'title': title,
                #         'message': message,
                #         'sticky': False,
                #     }
                # }

            query = """
                SELECT a.id, a.name,c.name user_name, d.name team_name
                FROM crm_lead a
                LEFT JOIN res_users b on a.user_id = b.id
                LEFT JOIN res_partner c on b.partner_id = c.id
                LEFT JOIN crm_team d on a.team_id = d.id
                WHERE a.phone = %s
                AND a.stage_id in (SELECT id FROM crm_stage WHERE is_won != TRUE)
                AND a.stage_id != 16
                AND a.active = TRUE
            """
            self.env.cr.execute(query, (str(vals.get('phone')),))
            res = self.env.cr.fetchall()
            team_name = ''
            # if res:
            #     for r in res:
            #         if r[3]:
            #             team_name = r[3]
            #     if vals.get('type_lead') != 'resale':
            #         message = _('Số điện thoại bị trùng đang chăm sóc bởi nhóm: ' + team_name)
            #         raise UserError(message)

            # if not validate_phone(vals.get('phone')):
            #     message = ''
            #     message += "- Số điện thoại:" + vals.get('phone') + "không phải là số Việt Nam"
            #     if message:
            #         raise UserError(message)
        else:
            message = _("Lead Bắt buộc phải có số điện thoại")
            raise UserError(message)
        lead = super(CRMLEAD, self).create(vals)
        if lead.phone:
            partner_ids = self.env['res.partner'].search(
                [('phone', '=', lead.phone)], limit=1)
            if partner_ids:
                for partner_id in partner_ids:
                    lead.partner_id = partner_id
            else:
                partner_id = self.env['res.partner'].create({
                    'name': lead.contact_name,
                    'phone': lead.phone,
                    'type': 'contact'
                })
                lead.partner_id = partner_id
        if lead.user_id.sale_team_id:
            lead.team_id = lead.user_id.sale_team_id
        return lead

    @api.onchange('phone')
    def onchange_check_exist(self):
        if self.phone:
            lead_exist_ids = self.env['crm.lead'].sudo().search(
                [('phone', '=', self.phone), ('id', '!=', self.env.context.get('active_ids'))])
            if lead_exist_ids:
                for lead_exist_id in lead_exist_ids:
                    if lead_exist_id.id != self.env.context.get('active_ids'):
                        self.lead_exist_ids.create({
                            'lead_id': self.id,
                            'lead_exist_id': lead_exist_id.id,
                        })
            else:
                self.lead_exist_ids.unlink()
            partner_ids = self.env['res.partner'].sudo().search(
                [('phone', '=', self.phone)], limit=1)
            if partner_ids:
                for partner_id in partner_ids:
                    self.partner_id = partner_id

    def action_new_booking(self):
        action = self.env.ref("vtg_custom_lead.vtg_crm_lead_booking_action_new").read()[0]
        if not  self.booking_ids:
            action['context'] = {
                'search_default_lead_id': self.id,
                'default_lead_id': self.id,
                'search_default_partner_id': self.partner_id.id,
                'default_partner_id': self.partner_id.id,
                'default_team_id': self.team_id.id,
                'default_user_id': self.user_id.id,
                'default_source_id': self.source_id.id,
                'default_channel_id': self.channel_id.id,
            }
        else:
            action['res_id'] = self.booking_ids[0].id
        return action

    @api.depends('user_id', 'type')
    def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for lead in self:
            # setting user as void should not trigger a new team computation
            if not lead.user_id:
                continue
            user = lead.user_id
            if lead.team_id and user in (lead.team_id.member_ids | lead.team_id.user_id):
                continue
            team_domain = [('use_leads', '=', True)] if lead.type == 'lead' else [('use_opportunities', '=', True)]
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=team_domain)
            # lead.team_id = team.id

    @api.model
    def _get_duplicated_leads_by_phone(self, partner_id, phone, include_lost=False):
        """ Search for opportunities that have the same partner and that arent done or cancelled """
        if not phone:
            return self.env['crm.lead']
        partner_match_domain = []
        for email in [phone]:
            partner_match_domain.append(('phone', '=ilike', phone))
        if partner_id:
            partner_match_domain.append(('partner_id', '=', partner_id))
        partner_match_domain = ['|'] * (len(partner_match_domain) - 1) + partner_match_domain
        if not partner_match_domain:
            return self.env['crm.lead']
        domain = partner_match_domain
        if not include_lost:
            domain += ['&', ('active', '=', True), ('probability', '<', 100)]
        else:
            domain += ['|', '&', ('type', '=', 'lead'), ('active', '=', True), ('type', '=', 'opportunity')]
        return self.search(domain)

    def vtg_crm_lead_log_note_action_new(self):
        view_id = self.env.ref('vtg_custom_lead.vtg_crm_lead_log_note_form_view').id
        ctx = dict(
            default_lead_id=self.id,
            default_stage_id=self.stage_id.id,
        )
        return {
            'name': _('Ghi chú'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.lead.log.note',
            'view_id': view_id,
            'target': 'new',
            'context': ctx,
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }

    def check_lead_log_note_action(self, lead_id, stage_id):
        note = self.env['crm.lead.log.note'].search([('lead_id', '=', lead_id.id), ('stage_id', '=', stage_id.id)])
        return note

    def write(self, vals):
        for lead_id in self:
            stage_id_old = lead_id.stage_id.id
            user_old_id = lead_id.user_id
            stage_old = lead_id.stage_id
            res = super(CRMLEAD, self).write(vals)
            stage_id_new = lead_id.stage_id.id
            stage_new = lead_id.stage_id
            user_new_id = lead_id.user_id
            if stage_id_old != stage_id_new and stage_old.sequence < stage_new.sequence:
                note = lead_id.check_lead_log_note_action(lead_id, stage_old)
                if not note:
                    raise UserError("Bạn vui lòng cập nhật ghi chú trước khi chuyển trạng thái")
            if user_old_id != user_new_id:
                lead_id.partner_id.user_id = user_new_id
                lead_id.partner_id.team_id = user_new_id.sale_team_id
            return res

    def _handle_salesmen_assignment(self, user_ids=False, team_id=False):
        res = super(CRMLEAD, self)._handle_salesmen_assignment(user_ids, team_id)
        if len(self.user_id) == 1:
            self.partner_id.user_id = self.user_id
            self.partner_id.team_id = self.team_id
        return res

    def action_auto_recall(self):
        lead_ids = self.env['crm.lead'].search(
            [('stage_id', '=', 16), ('date_open', '<', datetime.now() - relativedelta(days=7)),
             ('is_recall', '=', False)])
        for lead_id in lead_ids:
            lead_id.is_recall = True
            lead_id.active = False


class CRMLEADLOGCALL(models.Model):
    _name = 'crm.lead.log.call'

    sequence = fields.Integer()
    lead_id = fields.Many2one('crm.lead', string='Cơ hội')
    note = fields.Char('Ghi chú')
    status = fields.Char(track_visibility='onchange', string='Tình trạng')


class CRMLEADexist(models.Model):
    _name = 'crm.lead.exist'

    lead_id = fields.Many2one('crm.lead', string='Lead hiện tại')
    lead_exist_id = fields.Many2one('crm.lead', string='Lead đang trùng')
    stage_id = fields.Many2one('crm.stage', string='Trạng thái', related="lead_exist_id.stage_id")
    user_id = fields.Many2one('res.users', string='Nhân viên kinh doanh', related="lead_exist_id.user_id")
    team_id = fields.Many2one('crm.team', string='Nhóm kinh doanh', related="lead_exist_id.team_id")


class Lead2OpportunityMassConvert(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner.mass'

    @api.depends('user_ids')
    def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for convert in self:
            # setting user as void should not trigger a new team computation
            if not convert.user_id and not convert.user_ids and convert.team_id:
                continue
            user = convert.user_id or convert.user_ids and convert.user_ids[0] or self.env.user
            if convert.team_id and user in convert.team_id.member_ids | convert.team_id.user_id:
                continue
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=None)
            convert.team_id = None


class Lead2OpportunityConvert(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    @api.depends('duplicated_lead_ids')
    def _compute_name(self):
        for convert in self:
            if not convert.name:
                convert.name = 'convert' if convert.duplicated_lead_ids and len(
                    convert.duplicated_lead_ids) >= 2 else 'convert'


class RESPARTNER(models.Model):
    _inherit = 'res.partner'

    def name_get(self):
        res = []
        for partner in self:
            phone = partner.phone and partner.phone or ''
            name = partner.name and partner.name or ''
            res.append((partner.id, f"{phone}-{name}"))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('phone', operator, name), ('name', operator, name)]
        partner = self.search(domain + args, limit=limit)
        return partner.name_get()


class CRMLEADLOGNOTE(models.Model):
    _name = 'crm.lead.log.note'

    lead_id = fields.Many2one('crm.lead', string='Cơ hội')
    stage_id = fields.Many2one('crm.stage', string="Trạng thái")
    note = fields.Char('Ghi chú')
    content = fields.Selection([('pre_sale', 'Tư vấn trước bán'), ('after_sale', 'Chăm sóc sau bán')],
                               string="Nội dung liên hệ",
                               default='pre_sale')
    contact_form = fields.Selection(
        [('video', 'Video Call'),
         ('tele_sale', 'Tele sale'),
         # ('chat', 'Chat'),
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

    @api.model
    def create(self, vals):
        note = super(CRMLEADLOGNOTE, self).create(vals)
        content = ''
        if note.content == 'pre_sale':
            content = 'Tư vấn trước bán'
        elif note.content == 'after_sale':
            content = 'Chăm sóc sau bán'

        contact_form = ''
        if note.contact_form == 'video':
            contact_form = 'Video Call'
        elif note.contact_form == 'tele_sale':
            contact_form = 'Tele sale'
        elif note.contact_form == 'chat':
            contact_form = 'Chat'
        elif note.contact_form == 'meeting':
            contact_form = 'Gặp mặt'
        elif note.contact_form == 'other':
            contact_form = 'Khác'

        result = ''
        if note.result == 'interacted':
            result = 'Đã tương tác'
        elif note.result == 'no_answer':
            result = 'Không trả lời'
        elif note.result == 'call_back':
            result = 'Gọi lại sau'
        elif note.result == 'cancel_meeting':
            result = 'Hủy gặp'
        elif note.result == 'other':
            result = 'Khác'

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

        note.lead_id.message_post(body=chatter_message)

        return note


class HistoryUser(models.Model):
    _name = 'crm.lead.history.recall'

    lead_id = fields.Many2one('crm.lead')
    user_id = fields.Many2one('res.users', string='Nhân vên')
    team_id = fields.Many2one('crm.team', string='Nhóm')
    reason = fields.Text('Lý do thu hồi')
    date_time = fields.Datetime('Thời gian thu hồi')
