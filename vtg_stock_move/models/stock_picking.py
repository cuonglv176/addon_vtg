from odoo import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_sale_user_id = fields.Many2one('res.users', string='Nhân viên Sale')

