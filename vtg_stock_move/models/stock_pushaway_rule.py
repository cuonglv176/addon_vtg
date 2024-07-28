from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPushAwayRule(models.Model):
    _name = 'stock.pushaway.rule'
    _description = "Push away rule"

    sequence = fields.Integer('Priority', help="Give to the more specialized category, a higher priority to have them in top of the list.")
    product_id = fields.Many2one('product.product', 'Product')
    category_id = fields.Many2one('product.category', 'Product Category')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    location_in_id = fields.Many2one(
        'stock.location', 'Location In', check_company=True,
        domain="[('child_ids', '!=', False), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        required=True, ondelete='cascade', index=True)
    location_out_id = fields.Many2one(
        'stock.location', 'Location Out', check_company=True,
        domain="[('id', 'child_of', location_in_id), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        required=True, ondelete='cascade')
