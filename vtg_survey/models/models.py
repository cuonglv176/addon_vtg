# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from werkzeug import urls


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    state = fields.Selection([
        ('new', 'Not started yet'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed')], string='Status', default='in_progress', readonly=True)

    def _mark_done(self):
        user_input = super(SurveyUserInput, self)._mark_done()
        name = ''
        phone = ''
        toc = ''
        cong_viec = ''
        tuoi = ''
        mat = ''
        for line_id in self.user_input_line_ids:
            if line_id.question_id.title == '5- Tên thường gọi của anh là:':
                name = line_id.value_char_box or ''
            if line_id.question_id.title == '6- Số điện thoại sử dụng thường xuyên của anh là:':
                phone = line_id.value_char_box or ''
            if line_id.question_id.title == '1- Tóc của anh trông như thế nào ạ ?':
                toc = line_id.suggested_answer_id.value or ''
            if line_id.question_id.title == '2-  Anh đang làm công việc gì ạ?':
                cong_viec = line_id.suggested_answer_id.value or ''
            if line_id.question_id.title == '3- Năm nay anh bao nhiêu tuổi ạ?':
                tuoi = line_id.suggested_answer_id.value or ''
            if line_id.question_id.title == '4- Khuôn mặt của anh phù hợp với kiểu nào nhất ạ?':
                mat = line_id.suggested_answer_id.value or ''
        partner_id = self.env['res.partner'].sudo().search([('phone', '=', phone)])
        cong_viec_id = self.env['crm.lead.job'].sudo().search([('name', '=', cong_viec)])
        status_selection = None
        if toc == 'Trán cao':
            status_selection = 'high_forehead'
        if toc == 'Hói đỉnh':
            status_selection = 'bald_peak'
        if toc == 'Tóc thưa':
            status_selection = 'thinning_hair'
        if toc == 'Rụng Cả Đầu':
            status_selection = 'whole_head'

        # ('high_forehead', 'Trán cao'),
        # ('bald_peak', 'Hói đỉnh'),
        # ('bald_peak', 'Tóc thưa'),
        # ('whole_head', 'Rụng Cả Đầu')
        if not self.order_id:
            lead_id = self.env['crm.lead'].sudo().create({
                'name': name,
                'partner_id': partner_id.id or None,
                'team_id': self.survey_id.user_id.sale_team_id.id,
                'user_id': self.survey_id.user_id.id,
                'marketing_id': self.survey_id.user_id.id,
                'department_id': self.survey_id.user_id.employee_id.department_id.id,
                'description': 'Khuôn mặt: ' + mat,
                'source_id': 10,
                'channel_id': 1,
                'job_id': cong_viec_id.id,
                'phone': phone,
                'year_old': tuoi,
                'contact_name': name,
                'status_selection': status_selection,
                'demand_selection': None,
            })
        return user_input

    order_id = fields.Many2one('sale.order', string='Trial Drive Request')


class Survey(models.Model):
    _inherit = 'survey.survey'

    survey_order = fields.Boolean(string='Survey order')

    def _compute_survey_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for r in self:
            if self._context.get('order_id'):
                r.public_url = urls.url_join(base_url, '/vtg/survey/start/%s/%s' % (
                    r.access_token, self._context['order_id']))
            else:
                super(Survey, self)._compute_survey_url()

    def _create_answer(self, user=False, partner=False, email=False, test_entry=False, check_attempts=True,
                       **additional_vals):
        answers = super(Survey, self)._create_answer(user=user, partner=partner, email=email,
                                                     test_entry=test_entry, check_attempts=check_attempts,
                                                     **additional_vals)
        if self._context.get('order_id'):
            answers.order_id = self._context['order_id']
        return answers


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_url_survey = fields.Char(string='URL khảo sát')
    survey_id = fields.Many2one('survey.survey', string='Mẫu khảo sát')
    answer_ids = fields.One2many('survey.user_input', 'order_id', string='Trả lời khảo sát')

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.survey_id = self.env['survey.survey'].sudo().search([('survey_order', '=', True)], limit=1)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.x_url_survey = urls.url_join(base_url,
                                          '/vtg/survey/start/%s/%s' % (self.survey_id.access_token, self.id))
        return res

class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    x_url_survey = fields.Char(string='URL khảo sát', compute="get_x_url_survey")

    @api.depends('sale_id.x_url_survey')
    def get_x_url_survey(self):
        for s in self:
            if s.sale_id.x_url_survey:
                s.x_url_survey = s.sale_id.x_url_survey
            else:
                s.x_url_survey = ''

