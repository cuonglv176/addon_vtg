# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request
import werkzeug
from odoo.addons.survey.controllers.main import Survey


class Survey(Survey):
    @http.route('/vtg/survey/start/<string:survey_token>/<int:order_id>', type='http',
                auth='public', website=True)
    def order_survey_start(self, survey_token, order_id, answer_token=None, email=False, **post):
        access_data = self._get_access_data(survey_token, answer_token, ensure_token=False)
        if access_data['validity_code'] is not True:
            return self._redirect_with_error(access_data, access_data['validity_code'])

        survey_sudo, answer_sudo = access_data['survey_sudo'], access_data['answer_sudo']
        if not answer_sudo:
            try:
                answer_sudo = survey_sudo.with_context(
                    {'order_id': order_id})._create_answer(user=request.env.user,
                                                           email=email)
            except UserError:
                answer_sudo = False

        # check customer has surveyed trail driver
        order_obj = request.env['sale.order'].sudo().search([
            ('id', '=', order_id)
        ])
        if order_obj:
            if order_obj.answer_ids.filtered(lambda t: t.state in ['done']):
                data = {'survey': survey_sudo, 'answer': answer_sudo, 'page': 0}
                return request.render('survey.sfinished', data)

        if not answer_sudo:
            try:
                survey_sudo.with_user(request.env.user).check_access_rights('read')
                survey_sudo.with_user(request.env.user).check_access_rule('read')
            except:
                return werkzeug.utils.redirect("/")
            else:
                return request.render("survey.403", {'survey': survey_sudo})

        # Select the right page
        if answer_sudo.state == 'new':  # Intro page
            data = {'survey': survey_sudo, 'answer': answer_sudo, 'page': 0}
            return request.render('survey.survey_init', data)
        else:
            return request.redirect('/survey/%s/%s' % (survey_sudo.access_token, answer_sudo.access_token))
