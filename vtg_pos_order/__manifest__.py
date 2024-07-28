# -*- coding: utf-8 -*-
{
    'name': "VTG POS",

    'summary': """VTG POS""",

    'description': """
        Customize order line in pos
    """,

    'author': "TuUH",
    'website': "",

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale','mail'],

    # always loaded
    'data': [
        # 'views/pos_order_line.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'vtg_pos_order/static/src/js/**/*',
        ],
        'web.assets_qweb': [
            'vtg_pos_order/static/src/xml/**/*',
        ],
        'web.assets_backend': [
            'vtg_pos_order/static/src/css/**/*',
        ],
    },
}
