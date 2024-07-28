# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
from collections import defaultdict
from datetime import datetime, timedelta
import logging
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class DiscussController(http.Controller):
    # --------------------------------------------------------------------------
    # Thread API (channel/chatter common)
    # --------------------------------------------------------------------------

    @http.route('/mail/message/post', methods=['POST'], type='json', auth='public')
    def mail_message_post(self, thread_model, thread_id, post_data, **kwargs):
        if thread_model == 'mail.channel':
            channel_partner_sudo = request.env['mail.channel.partner']._get_as_sudo_from_request_or_raise(request=request, channel_id=int(thread_id))
            thread = channel_partner_sudo.channel_id
        else:
            thread = request.env[thread_model].browse(int(thread_id)).exists()
        allowed_params = {'attachment_ids', 'body', 'message_type', 'partner_ids', 'subtype_xmlid', 'parent_id'}
        _logger.info("post_data.items() >>>>>>>>>>>>>>>>>>>>>>")
        _logger.info(post_data.items())
        self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
                                                           [3],
                                                           f'Bạn được nhắc tới: ',
                                                           thread_model, thread_id,
                                                           datetime.now())
        return thread.message_post(**{key: value for key, value in post_data.items() if key in allowed_params}).message_format()[0]
