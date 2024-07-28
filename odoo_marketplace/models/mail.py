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
from odoo import fields, models, SUPERUSER_ID

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    message_attachment_count = fields.Integer('Attachment Count', compute='_compute_message_attachment_count', groups="base.group_user,odoo_marketplace.marketplace_draft_seller_group")
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', groups='base.group_user,odoo_marketplace.marketplace_draft_seller_group')
