# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Fixed Header List View',
    'version': '15.0.1.0.0',
    'sequence': 1,
    'summary': """
        Set Fix Header List, Set Fix Header Tree, Set Permanent Header List, Web Sticky Header List, Freeze Header List, 
        Set Fix Header, Set Permanent Header, Web Sticky Header, Freeze Header, Set Fix Header in List, Set Permanent Header in List, 
        Web Sticky Header in List, Freeze Header in List, Set Fix List Header, Set Permanent List Header, Web Sticky List Header, 
        Freeze List Header, All in one Fix Header, All in one Permanent Header, All in one Web Sticky Header List, Frozen Header Frozen,
        All in one Freeze Header List, All in one Sticky Tree Header, All in one Sticky List Header, All ine One Sticky View List,
        List View Manager ListView Manager, Sticky Tree View Fixed Tree View, All in one Tree View, Fix List Header Table, Fixed Table Header, 
    """,
    'description': "Fixed Header List View is very useful for displaying list headers within Odoo.",
    'author': 'NEWAY Solutions',
    'maintainer': 'NEWAY Solutions',
    'price': '0.0',
    'currency': 'USD',
    'website': 'https://neway-solutions.com',
    'license': 'LGPL-3',
    'images': [
        'static/description/screenshot.gif'    
    ],
    'depends': [
        'web'
    ],
    'data': [
        
    ],
    'assets': {
        'web.assets_backend': [
            'fixed_header_list/static/src/scss/list.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
