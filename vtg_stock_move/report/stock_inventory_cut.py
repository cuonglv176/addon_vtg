# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleReport(models.Model):
    _name = "stock.inventory.cut"
    _description = "Stock Inventory Cut Report"
    _auto = False
    _rec_name = "user_id"

    user_id = fields.Many2one('res.users', 'Nhân viên Sale', readonly=True)
    location_id = fields.Many2one('stock.location', 'Kho', readonly=True)
    product_id = fields.Many2one('product.product', 'Sản phẩm', readonly=True)
    quantity = fields.Float('Tồn kho', readonly=True)

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        query = """
            select row_number() over (order by dataa.location_id, dataa.user_id, dataa.product_id) as id, 
                    dataa.location_id, 
                    dataa.user_id,
                    dataa.product_id, 
                    sum(dataa.quantity_done) quantity
            from (
                -- nhập kho 
                select sl.id location_id, sp.x_sale_user_id user_id, sm.product_id, 
                        sum(sm.product_uom_qty) quantity_done 
                        from stock_move sm
                left join stock_picking sp on sp.id = sm.picking_id 
                left join stock_location sl on sl.id = sm.location_dest_id
                left join product_product pp on pp.id = sm.product_id
                left join product_template pt on pt.id = pp.product_tmpl_id
                where sl.name = 'HÀNG ĐÃ CẮT'
                and sm.state not in ('done', 'cancel')
                and sp.x_sale_user_id is not null
                and pt.detailed_type = 'product'
                and sp.id in (select distinct so.x_cut_transfer_picking_id 
                                from sale_order so 
                                where so.state in ('sale', 'done') 
                                and so.x_cut_transfer_picking_id is not null
                                and 'done' in (select sp2.state from stock_picking sp2 where sp2.sale_id = so.id)
                                )
                group by sl.id, sp.x_sale_user_id, sm.product_id
                
                -- union all
                -- xuất kho
                -- select sl.id location_id, sp.x_sale_user_id, sml.product_id, sum(-sml.qty_done) quantity_done from stock_move_line sml 
                -- left join stock_picking sp on sp.id = sml.picking_id 
                -- left join stock_location sl on sl.id = sml.location_id
                -- where sl.name = 'HÀNG ĐÃ CẮT'
                -- and sml.state = 'done'
                -- and sp.x_sale_user_id is not null
                -- group by sl.id, sp.x_sale_user_id, sml.product_id
            ) as dataa
            group by dataa.location_id, dataa.user_id, dataa.product_id
            having sum(dataa.quantity_done) != 0
        """
        return query

    def action_view_order(self):
        # picking_ids = self.env['stock.picking'].sudo().search(
        #     [('x_sale_user_id', '=', self.user_id.id), ('location_dest_id', '=', self.location_id.id),
        #      ('state', 'not in', ('done', 'cancel'))])

        self._cr.execute("""
            select sm.picking_id
                from stock_move sm
                left join stock_picking sp on sp.id = sm.picking_id 
                left join stock_location sl on sl.id = sm.location_dest_id
                left join product_product pp on pp.id = sm.product_id
                left join product_template pt on pt.id = pp.product_tmpl_id
                where sl.id = %s
                and sm.state not in ('done', 'cancel')
                and sp.x_sale_user_id = %s
                and pt.detailed_type = 'product'
                and pp.id = %s
                and sp.id in (select distinct so.x_cut_transfer_picking_id 
                                from sale_order so 
                                where so.state in ('sale', 'done') 
                                and so.x_cut_transfer_picking_id is not null
                                and 'done' in (select sp2.state from stock_picking sp2 where sp2.sale_id = so.id)
                                )
                and sm.product_uom_qty > 0
        """, (self.location_id.id, self.user_id.id, self.product_id.id, ))
        result = [data[0] for data in self._cr.fetchall()]
        order_cut = self.env['sale.order'].sudo().search(
            [('x_cut_transfer_picking_id', 'in', result)])
        action = self.env.ref('sale.action_orders').sudo().read()[0]
        domain = safe_eval(action['domain'])
        try:
            domain.append(('id', 'in', order_cut.ids))
        except:
            return action

        action['domain'] = domain
        return action
