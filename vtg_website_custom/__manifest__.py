# -*- coding: utf-8 -*-
{
    'name': "Web custom",

    'summary': """
        Web custom""",

    'description': """
        Web custom
    """,

    'author': "CuonglV",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web'],

    # always loaded
    'data': [
        # 'views/assets.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'vtg_website_custom/static/src/scss/style.scss',
        ],
    },

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
