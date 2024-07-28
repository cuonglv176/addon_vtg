# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)
from odoo import http

class VTGNTD(http.Controller):

    @http.route('/survey/ntd', type="http", auth="public", website="True")
    def vtg_survey_ntd(self, **post):
        return request.redirect('/survey/start/75bfbe89-864f-4bcc-83b6-6192807190a3')

    @http.route('/survey/ntd1', type="http", auth="public", website="True")
    def vtg_survey_ntd1(self, **post):
        return request.redirect('/survey/start/573f0903-9e48-4f77-a26c-f9c8468cf075')
