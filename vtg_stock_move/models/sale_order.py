from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_cut_transfer_picking_id = fields.Many2one('stock.picking', 'Cut transfer', copy=0)
    x_need_cut_transfer = fields.Boolean('Need cut transfer', compute="_compute_need_cut_transfer")
    x_cut_state = fields.Selection([
        # ('no_need_cut', 'No Need Cut'),
        ('not_cut_yet', 'Not Cut yet'),
        ('cut', 'Cut')
    ], string='Cut State', compute="_compute_cut_state", store=True, copy=0)

    @api.depends('x_need_cut_transfer', 'x_cut_transfer_picking_id.state')
    def _compute_cut_state(self):
        for order in self:
            if not order.x_need_cut_transfer:
                order.x_cut_state = None
            elif order.x_cut_transfer_picking_id.state == 'done':
                order.x_cut_state = 'cut'
            else:
                order.x_cut_state = 'not_cut_yet'

    def _compute_need_cut_transfer(self):
        for order in self:
            if not order.order_line.filtered(
                    lambda l: l.product_id.categ_id.name and l.product_id.categ_id.name.upper() in ('SẢN PHẨM TÓC', 'HÀNG ĐẶT RIÊNG')):
                order.x_need_cut_transfer = False
            else:
                order.x_need_cut_transfer = True

    @api.onchange('x_branch_id')
    def onchange_branch_default_warehouse(self):
        if not self.x_branch_id:
            pass
        default_warehouse_id = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id), ('x_branch_id', '=', self.x_branch_id.id)], limit=1)
        if default_warehouse_id:
            self.warehouse_id = default_warehouse_id
        return {'warehouse_id': [
            ('company_id', '=', self.env.company.id),
            ('x_branch_id', '=', self.x_branch_id.id),
        ]}

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        res.onchange_branch_default_warehouse()
        return res

    def action_transfer_cut_location(self):
        if self.x_cut_transfer_picking_id:
            raise ValidationError(_('This order was created cut transfer'))
        location_src_id = self.warehouse_id.lot_stock_id
        location_dest_id = None
        move_vals = []
        for line in self.order_line:
            # TODO: nghĩ phương án check khác
            if not line.product_id.categ_id.name or line.product_id.categ_id.name.upper() not in ('SẢN PHẨM TÓC', 'HÀNG ĐẶT RIÊNG'):
                continue
            if not location_src_id.location_id:
                continue
            pushaway_rule_id = self.env['stock.pushaway.rule'].sudo().search(
                [('location_in_id', '=', location_src_id.location_id.id),
                 '|',
                 '&', ('product_id', '!=', False), ('product_id', '=', line.product_id.id),
                 '&', ('category_id', '!=', False), ('category_id', '=', line.product_id.categ_id.id)
                 ], order='sequence')
            if not pushaway_rule_id:
                continue
            move_vals.append((0, 0, {
                'product_id': line.product_id.id,
                'name': line.product_id.display_name,
                'date': fields.Datetime.now(),
                'description_picking': line.product_id.name,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'location_id': location_src_id.id,
                'location_dest_id': pushaway_rule_id.location_out_id.id,
            }))
            location_dest_id = pushaway_rule_id.location_out_id
        if move_vals and location_dest_id:
            picking_type_id = self.env['stock.picking.type'].with_context(active_test=False).search(
                [('warehouse_id', '=', self.warehouse_id.id), ('sequence_code', '=', 'INT')])
            if len(picking_type_id) > 1:
                raise ValidationError(_('Please config only 1 Picking type transfer with code INT for 1 warehouse!'))
            picking_id = self.env['stock.picking'].create({
                'picking_type_id': picking_type_id.id,
                'location_id': location_src_id.id,
                'location_dest_id': location_dest_id.id,
                'x_location_id': location_src_id.id,
                'x_location_dest_id': location_dest_id.id,
                'move_ids_without_package': move_vals,
                'x_sale_user_id': self.user_id.id if self.user_id else None,
            })
            self.x_cut_transfer_picking_id = picking_id
            picking_id.with_context(cancel_backorder=False, auto_confirm=True)._action_done()
