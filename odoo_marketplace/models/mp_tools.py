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
from odoo import _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

def check_mp_officer(method):

    def auth_method(self, *args):
        if not self.env.user.check_user_is_mp_officer():
            raise UserError(_("You are not an authorized user to change seller account details. Please contact your administrator. "))
        return method(self, *args)
    return auth_method
