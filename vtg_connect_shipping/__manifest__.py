# -*- coding: utf-8 -*-
{
    'name': "VTG Connect Shipping",

    'summary': """Shipping""",

    'description': """
        Customize booking in pos
    """,

    'author': "TuUH",
    'website': "",

    # any module necessary for this one to work correctly
    'depends': ['base', 'vtg_custom_lead'],

    # always loaded
    'data': [
        'views/view.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {

    },
}
