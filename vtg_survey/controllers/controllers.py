# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)
from odoo import http

class VTG(http.Controller):

    @http.route('/survey/huy', type="http", auth="public", website="True")
    def vtg_survey(self, **post):
        return request.redirect('/survey/start/aff43818-5974-4933-8a15-9c3043e30903')