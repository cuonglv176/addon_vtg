# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError


class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = 'applicant.get.refuse.reason'
    _description = 'Get Refuse Reason'

    def action_refuse_reason_apply(self):
        if self.send_mail:
            if not self.template_id:
                raise UserError(_("Email template must be selected to send a mail"))
            if not self.applicant_ids.filtered(lambda x: x.email_from or x.partner_id.email):
                raise UserError(_("Email of the applicant is not set, email won't be sent."))
        self.applicant_ids.write({'refuse_reason_id': self.refuse_reason_id.id, 'stage_id': 12})
        if self.send_mail:
            applicants = self.applicant_ids.filtered(lambda x: x.email_from or x.partner_id.email)
            applicants.with_context(active_test=True).message_post_with_template(self.template_id.id, **{
                'auto_delete_message': True,
                'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                'email_layout_xmlid': 'mail.mail_notification_light'
            })

class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    status_id = fields.Many2one('hr.applicant.status', string='Trạng thái')
    note_ids = fields.One2many('hr.applicant.log.note','applicant_id',string='Log note')

    def vtg_hr_applicant_log_note_action_new(self):
        view_id = self.env.ref('vtg_hr_recruitment.hr_applicant_log_note_form_view').id
        ctx = dict(
            default_applicant_id=self.id,
        )
        return {
            'name': _('Ghi chú'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.applicant.log.note',
            'view_id': view_id,
            'target': 'new',
            'context': ctx,
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }

class HrApplicantStatus(models.Model):
    _name = 'hr.applicant.status'

    name = fields.Char(string='Tên')
    applicant_id = fields.Many2one('hr.applicant', string='Tuyển dụng')
    stage_ids = fields.Many2many('hr.recruitment.stage', string='Giai đoạn')

class HrApplicantLognote(models.Model):
    _name = 'hr.applicant.log.note'

    applicant_id = fields.Many2one('hr.applicant', string='Tuyển dụng')
    name = fields.Char(string='Tên')
    note = fields.Text(string='Mô tả')
    content = fields.Selection([('enter_profile', 'Nhập nội dung'),
                                ('filter_profiles', 'Lọc hồ sơ'),
                                ('interview', 'Hẹn phỏng vấn'),
                                ('offer', 'Offer'),
                                ('job', 'Hẹn nhận việc'),
                                ('review', 'Hẹn Review'),
                                ],
                               string="Nội dung thực hiện",
                               default='enter_profile')
    contact_form = fields.Selection(
        [('email', 'Email'),
         ('tele', 'Gọi điện'),
         ('chat', 'Chat'),
         ('meeting', 'Trực tiếp')],
        string="Hình thức liên hệ",
        default='email')
    result = fields.Selection(
        [
         ('no_answer', 'Không phản hồi'),
         ('success', 'Thành công'),
         ('failure', 'Thất bại'),
         ('other', 'Khác')],
        string="Kết quả",
        default='success')

    @api.model
    def create(self, vals):
        note = super(HrApplicantLognote, self).create(vals)
        content = ''
        if note.content == 'enter_profile':
            content = 'Nhập nội dung'
        elif note.content == 'filter_profiles':
            content = 'Lọc hồ sơ'
        elif note.content == 'interview':
            content = 'Hẹn phỏng vấn'
        elif note.content == 'offer':
            content = 'Offer'
        elif note.content == 'job':
            content = 'Hẹn nhận việc'
        elif note.content == 'review':
            content = 'Hẹn Review'

        contact_form = ''
        if note.contact_form == 'email':
            contact_form = 'Email'
        elif note.contact_form == 'tele':
            contact_form = 'Gọi điện'
        elif note.contact_form == 'chat':
            contact_form = 'Chat'
        elif note.contact_form == 'meeting':
            contact_form = 'Trực tiếp'
        elif note.contact_form == 'other':
            contact_form = 'Khác'
        result = ''
        if note.result == 'no_answer':
            result = 'Không phản hồi'
        elif note.result == 'success':
            result = 'Thành công'
        elif note.result == 'failure':
            result = 'Thất bại'
        elif note.result == 'other':
            result = 'Khác'

        chatter_message = _('''<b> Nội dung liên hệ: </b> %s <br/>
                                   <b> Hình thức liên hệ: </b> %s <br/>
                                   <b> Kết quả: </b> %s <br/>
                                   <b> Ghi chú: </b> %s <br/>
                                         ''') % (
            content,
            contact_form,
            result,
            note.note,
        )

        note.applicant_id.message_post(body=chatter_message)
        return note