# -*- coding: utf-8 -*-
{
    'name': "VTG Stock Move",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "CuongLV",
    'website': "",

    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'stock', 'sale_stock', 'vtg_security', 'crm'],

    # always loaded
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/stock_location.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
        'views/stock_pushaway_rule.xml',
        'report/stock_inventory_cut.xml',
    ],
}
