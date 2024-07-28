# -*- coding: utf-8 -*-
{
    'name': "VTG Notification",

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
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': {
            '/vtg_notification/static/src/js/systray.js',
        },
        'web.assets_qweb': {
            '/vtg_notification/static/src/xml/systray.xml',
        },
    },
}
