from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ResConfigCustom(models.TransientModel):
    _inherit = 'res.config.settings'

    x_allow_record_account_move = fields.Integer(related='company_id.x_allow_record_account_move', string='Allow access to the following journal entries', readonly=False)
