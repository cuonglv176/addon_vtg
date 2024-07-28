# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Fixed Header Kanban View',
    'version': '15.0.1.0.0',
    'sequence': 1,
    'summary': """
        Set Fix Header Kanban, Set Permanent Header Kanban, Web Sticky Header Kanban, Freeze Header Kanban, Set Fix Header, 
        Set Permanent Header, Web Sticky Header, Freeze Header, Set Fix Header in Kanban, Set Permanent Header in Kanban, 
        New Design Kanban View, New Style Kanban View, Web Responsive Kanban View, Advanced Kanban View, Odoo Kanban Odoo,
        Design Card View, Style Card, Responsive Card, Advanced Card Advanced, Advance Kanban Advance, Odoo Backend Kanban,
        Employee Kanban View, Employee KanbanView, Employee Card View, Advanced Employee CardView, All in one Web Sticky Header,
        Employees Kanban View, Employees KanbanView, Employees Card View, Advanced Employees CardView, Employee Navigator Kanban, 
        Contact Kanban View, Advanced Contact KanbanView, Contact Card View, Advanced Contact CardView, Fixed Header Frozen Card,
        Contacts Kanban View, Advanced Contacts KanbanView, Contacts Card View, Advanced Contacts CardView, Dynamic Kanban View, 
        Partner Kanban View, Advanced Partner KanbanView, Partner Card View, Advanced Partner CardView, All in one Freeze Header, 
        Partners Kanban View, Advanced Partners KanbanView, Partners Card View, Advanced Partners CardView, All in one Dynamic View, 
        Customer Kanban View, Advanced Customer KanbanView, Customer Card View, Advanced Customer CardView, All in one Kanban, 
        Customers Kanban View, Advanced Customers KanbanView, Customers Card View, Advanced Customers CardView, All in one Card, 
        HR Kanban View, Advanced HR KanbanView, HR Card View, Advanced HR CardView, Kanban View, KanbanView, Dynamic View,
        Elegant Kanban Employees Kanban, Elegant Card Employees Card, Elegant CardView Employees CardView, All in one Sticky View, 
        Web Sticky Header in Kanban, Freeze Header in Kanban, Set Fix Kanban Header, Set Permanent Kanban Header, Beautifu Kanban,
        Web Sticky Kanban Header, Freeze Kanban Header, All in one Fix Header, All in one Permanent Header, Frozen Header Kanban
    """,
    'description': "Fixed Header Kanban View is very useful for displaying kanban headers within Odoo.",
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
            'fixed_header_kanban/static/src/scss/kanban.scss',
        ],
    },
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
