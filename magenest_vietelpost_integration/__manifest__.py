# -*- coding: utf-8 -*-
{
    'name': "Viettel Post Integration",

    'summary': """
         Connect your Odoo with Viettel Post shipment""",

    'description': """
         Connect your Odoo with Viettel Post shipment
    """,

    'author': 'Magenest',
    'license': 'LGPL-3',
    'website': "https://magenest.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'product', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking_view.xml',
        'views/delivery_carrier_view.xml',
        'views/res_config_view.xml'
    ],
   'images': ['static/description/thumbnail.png'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
