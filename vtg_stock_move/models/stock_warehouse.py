from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_branch_id = fields.Many2one('vtg.branch', string='Chi nhánh')

