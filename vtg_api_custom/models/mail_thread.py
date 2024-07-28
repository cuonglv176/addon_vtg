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
import calendar
import logging

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *,
                     body='', subject=None, message_type='notification',
                     email_from=None, author_id=None, parent_id=False,
                     subtype_xmlid=None, subtype_id=False, partner_ids=None,
                     attachments=None, attachment_ids=None,
                     add_sign=True, record_name=False,
                     **kwargs):
        """ Post a new message in an existing thread, returning the new
            mail.message ID.
            :param str body: body of the message, usually raw HTML that will
                be sanitized
            :param str subject: subject of the message
            :param str message_type: see mail_message.message_type field. Can be anything but
                user_notification, reserved for message_notify
            :param int parent_id: handle thread formation
            :param int subtype_id: subtype_id of the message, used mainly use for
                followers notification mechanism;
            :param list(int) partner_ids: partner_ids to notify in addition to partners
                computed based on subtype / followers matching;
            :param list(tuple(str,str), tuple(str,str, dict) or int) attachments : list of attachment tuples in the form
                ``(name,content)`` or ``(name,content, info)``, where content is NOT base64 encoded
            :param list id attachment_ids: list of existing attachement to link to this message
                -Should only be setted by chatter
                -Attachement object attached to mail.compose.message(0) will be attached
                    to the related document.
            Extra keyword arguments will be used as default column values for the
            new mail.message record.
            :return int: ID of newly created mail.message
        """
        self.ensure_one()  # should always be posted on a record, use message_notify if no record
        # split message additional values from notify additional values
        msg_kwargs = dict((key, val) for key, val in kwargs.items() if key in self.env['mail.message']._fields)
        notif_kwargs = dict((key, val) for key, val in kwargs.items() if key not in msg_kwargs)

        # preliminary value safety check
        partner_ids = set(partner_ids or [])
        if self._name == 'mail.thread' or not self.id or message_type == 'user_notification':
            raise ValueError \
                (_('Posting a message should be done on a business document. Use message_notify to send a notification to an user.'))
        if 'channel_ids' in kwargs:
            raise ValueError \
                (_("Posting a message with channels as listeners is not supported since Odoo 14.3+. Please update code accordingly."))
        if 'model' in msg_kwargs or 'res_id' in msg_kwargs:
            raise ValueError \
                (_("message_post does not support model and res_id parameters anymore. Please call message_post on record."))
        if 'subtype' in kwargs:
            raise ValueError \
                (_("message_post does not support subtype parameter anymore. Please give a valid subtype_id or subtype_xmlid value instead."))
        if any(not isinstance(pc_id, int) for pc_id in partner_ids):
            raise ValueError(_('message_post partner_ids and must be integer list, not commands.'))

        self = self._fallback_lang()  # add lang to context imediatly since it will be usefull in various flows latter.

        # Explicit access rights check, because display_name is computed as sudo.
        self.check_access_rights('read')
        self.check_access_rule('read')
        record_name = record_name or self.display_name

        # Find the message's author
        if self.env.user._is_public() and 'guest' in self.env.context:
            author_guest_id = self.env.context['guest'].id
            author_id, email_from = False, False
        else:
            author_guest_id = False
            author_id, email_from = self._message_compute_author(author_id, email_from, raise_exception=True)

        if subtype_xmlid:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id(subtype_xmlid)
        if not subtype_id:
            subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

        # automatically subscribe recipients if asked to
        if self._context.get('mail_post_autofollow') and partner_ids:
            self.message_subscribe(partner_ids=list(partner_ids))

        parent_id = self._message_compute_parent_id(parent_id)

        values = dict(msg_kwargs)
        values.update({
            'author_id': author_id,
            'author_guest_id': author_guest_id,
            'email_from': email_from,
            'model': self._name,
            'res_id': self.id,
            'body': body,
            'subject': subject or False,
            'message_type': message_type,
            'parent_id': parent_id,
            'subtype_id': subtype_id,
            'partner_ids': partner_ids,
            'add_sign': add_sign,
            'record_name': record_name,
        })
        attachments = attachments or []
        attachment_ids = attachment_ids or []
        attachement_values = self._message_post_process_attachments(attachments, attachment_ids, values)
        values.update(attachement_values)  # attachement_ids, [body]

        new_message = self._message_create(values)

        # Set main attachment field if necessary
        self._message_set_main_attachment_id(values['attachment_ids'])

        if values['author_id'] and values['message_type'] != 'notification' and not self._context.get \
                    ('mail_create_nosubscribe'):
            if self.env['res.partner'].browse \
                        (values['author_id']).active:  # we dont want to add odoobot/inactive as a follower
                self._message_subscribe(partner_ids=[values['author_id']])
        self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
                                                           partner_ids,
                                                           self.env.user.partner_id.name + ' nhắc tới bạn trong: ' + self.name,
                                                           self._name, self.id,
                                                           datetime.now())
        self._message_post_after_hook(new_message, values)
        self._notify_thread(new_message, values, **notif_kwargs)
        return new_message
