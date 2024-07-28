# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    _description = 'Return Picking'

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super(ReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        vals['location_dest_id'] = return_line.move_id.location_id.id or self.location_id.id
        return vals

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        res = super(ReturnPicking, self)._onchange_picking_id()
        # check if only 1 location:
        all_location_id = []
        for move in self.product_return_moves.mapped('move_id'):
            if move.location_id.id in all_location_id:
                continue
            all_location_id.append(move.location_id.id)
        if len(all_location_id) > 1 or not all_location_id:
            return res
        self.location_id = all_location_id[0]
        return res
