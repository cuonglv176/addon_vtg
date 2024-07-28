# -*- coding: utf-8 -*-
{
    'name': "Custom Sale order",

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
    'depends': ['base', 'mail', 'sale', 'account', 'sale_crm', 'point_of_sale', 'product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_user_mass_views.xml',
        'report/commission_employee_report.xml',
        'views/product_product.xml',
    ],
}
