# -*- coding: utf-8 -*-
{
    'name': "Pos CRM",

    'summary': """POS CRM""",

    'description': """
        Customize booking in pos
    """,

    'author': "TuUH",
    'website': "",

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'vtg_custom_lead', 'sale'],

    # always loaded
    'data': [
        'views/booking.xml',
        'views/pos_order.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'vtg_pos_crm/static/src/js/**/*',
        ],
        'web.assets_qweb': [
            'vtg_pos_crm/static/src/xml/**/*',
        ],
    },
}
