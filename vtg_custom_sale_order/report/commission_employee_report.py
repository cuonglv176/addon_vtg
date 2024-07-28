# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class CommissionEmployeeReport(models.Model):
    _name = "commission.employee.report"
    _description = "Employee Commission Report"
    _auto = False

    order_name = fields.Char('Mã Đơn hàng', readonly=True)
    date_order = fields.Date('Ngày', readonly=True)
    product_id = fields.Many2one('product.product', 'Tên hàng/dịch vụ', readonly=True)
    product_categ_id = fields.Many2one('product.category', 'Nhóm hàng', readonly=True)
    user_id = fields.Many2one('res.users', 'Tên nhân viên', readonly=True)
    quantity = fields.Float('Số lượng', readonly=True)
    discounted_amount = fields.Float('Giá trị tính chiết khấu', readonly=True)
    rate = fields.Float('Hệ số', readonly=True)
    percent = fields.Float('(%)', readonly=True)
    calculate_amount = fields.Float('Giá trị tính', compute="_compute_calculate_amount")
    discount_amount = fields.Float('VND', readonly=True)

    def _compute_calculate_amount(self):
        for item in self:
            item.calculate_amount = item.discounted_amount * item.rate

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        sql = """
            select data.id,
                    data.order_name,
                    data.date_order,
                    pc.id product_categ_id,
                    pp.id product_id,
                    data.user_id,
                    data.quantity,
                    data.discounted_amount,
                    data.rate,
                    data.percent,
                    data.discount_amount
            from 
                (select
                    olu.id,
                    (case when olu.sale_line_id is not null then so.name
                        when olu.pos_line_id is not null then po.name
                        else NULL
                        end
                    ) order_name,
                    (case when olu.sale_line_id is not null then (so.date_order + interval '7 hours')::date
                        when olu.pos_line_id is not null then (po.date_order + interval '7 hours')::date
                        else NULL
                        end
                    ) date_order,
                    (case when olu.sale_line_id is not null then sol.product_id
                        when olu.pos_line_id is not null then pol.product_id
                        else NULL
                        end
                    ) product_id,
                    olu.user_id,
                    (case when olu.sale_line_id is not null then sol.product_uom_qty 
                        when olu.pos_line_id is not null then pol.qty
                        else NULL
                        end
                    ) quantity,
                    (case when olu.sale_line_id is not null then sol.price_total
                        when olu.pos_line_id is not null then pol.price_subtotal_incl
                        else NULL
                        end
                    ) discounted_amount,
                    coalesce(olu.rate, 1) rate,
                    (case when olu.discount_type = 'percent' then coalesce(olu.discount, 0)
                        else 0
                        end
                    ) percent,
                    coalesce(olu.amount, 0) discount_amount
                from order_line_user olu 
                left join sale_order_line sol on sol.id = olu.sale_line_id 
                left join sale_order so on so.id = sol.order_id 
                left join pos_order_line pol on pol.id = olu.pos_line_id 
                left join pos_order po on po.id = pol.order_id 
                where coalesce(olu.amount, 0) != 0
            ) as data
            left join product_product pp on pp.id = data.product_id 
            left join product_template pt on pt.id = pp.product_tmpl_id 
            left join product_category pc on pc.id = pt.categ_id 
        """
        return sql
