# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Lead Get',
    'summary': 'Generate Leads/Opportunities based on country, industries, size, etc.',
    'category': 'Sales/CRM',
    'version': '1.2',
    'depends': [
       'crm','vtg_custom_lead','hr'
    ],
    'data': [
        'views/views.xml',
    ],
    'auto_install': True,
    'assets': {
        'web.assets_backend': [
            'vtg_crm_get_lead/static/src/js/**/*',
        ],
        'web.assets_qweb': [
            'vtg_crm_get_lead/static/src/xml/**/*',
        ],
    },
}
