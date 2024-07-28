# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)
from odoo import http

class VTGNVT(http.Controller):

    @http.route('/survey/nvt', type="http", auth="public", website="True")
    def vtg_survey_nvt(self, **post):
        return request.redirect('/survey/start/8d4d7d43-e164-46eb-ae73-47d3b89996c6')

    @http.route('/survey/nvt1', type="http", auth="public", website="True")
    def vtg_survey_nvt1(self, **post):
        return request.redirect('/survey/start/ab509aa5-e5a8-4deb-8364-72213cff16e3')