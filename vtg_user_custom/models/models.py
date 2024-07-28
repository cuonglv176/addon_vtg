from odoo import models, fields, api, _
from odoo.exceptions import UserError


class vtgUserCustom(models.Model):
    _inherit = 'res.users'

    x_branch_id = fields.Many2one('vtg.branch', string='Chi nhánh')


class vtgSaleOrderCustom(models.Model):
    _inherit = 'sale.order'

    x_branch_id = fields.Many2one('vtg.branch', string='Chi nhánh')

class vtgSaleOrderLineCustom(models.Model):
    _inherit = 'sale.order.line'

    x_branch_id = fields.Many2one('vtg.branch', string='Chi nhánh', compute="_update_sale_order_x_branch_id", store=True)

    @api.depends('order_id')
    def _update_sale_order_x_branch_id(self):
        for s in self:
            s.x_branch_id = s.order_id.x_branch_id

class vtgResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    access_ids = fields.Many2many('res.users', string='User được quyền truy cập',
                                  relation='res_partner_user_access_rel')

class AccountMove(models.Model):
    _inherit = 'account.move'

    branch_id = fields.Many2one('vtg.branch', string='Chi nhánh', compute="_get_branch", store=True)

    @api.depends('sale_id.x_branch_id')
    def _get_branch(self):
        for s in self:
            if s.sale_id:
                s.branch_id = s.sale_id.x_branch_id
