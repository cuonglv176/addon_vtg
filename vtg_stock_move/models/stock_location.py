from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    x_branch_id = fields.Many2one('vtg.branch', string='Chi nhánh')

