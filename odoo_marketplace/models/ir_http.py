# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
from odoo import api, models
from odoo.http import request
from odoo.tools import ustr
from odoo.addons.web.controllers.main import HomeStaticTemplateHelpers

import json
import hashlib
import odoo

import logging
_logger = logging.getLogger(__name__)

class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        session_info = super(Http, self).session_info()
        user = request.env.user

        if user.check_user_is_draft_seller() or user.check_user_is_seller():
            user_context = request.session.get_context() if request.session.uid else {}
            mods = odoo.conf.server_wide_modules or []
            qweb_checksum = HomeStaticTemplateHelpers.get_qweb_templates_checksum(addons=mods, debug=request.session.debug)
            lang = user_context.get("lang")
            translations_per_module, lang_params = request.env['ir.translation'].get_translations_for_webclient(mods, lang)
            translation_cache = {
                'lang': lang,
                'lang_parameters': lang_params,
                'modules': translations_per_module,
                'multi_lang': len(request.env['res.lang'].sudo().get_installed()) > 1,
            }
            menu_json_utf8 = json.dumps({ str(k): v for k, v in request.env['ir.ui.menu'].load_menus(request.session.debug).items()}, default=ustr, sort_keys=True).encode()
            translations_json_utf8 = json.dumps(translation_cache, sort_keys=True).encode()
            cache_hashes = {
                "load_menus": hashlib.sha1(menu_json_utf8).hexdigest(),
                "qweb": qweb_checksum,
                "translations": hashlib.sha1(translations_json_utf8).hexdigest(),
            }
            session_info.update({
                "user_companies": {'current_company': user.company_id.id, 'allowed_companies': {comp.id:{'id':comp.id,'name': comp.name} for comp in user.company_ids}},
                "currencies": self.get_currencies(),
                "show_effect": True,
                "display_switch_company_menu": user.has_group('base.group_multi_company') and len(user.company_ids) > 1,
                "cache_hashes": cache_hashes,
            })
        return session_info
