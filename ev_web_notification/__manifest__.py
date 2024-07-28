# -*- coding: utf-8 -*-

{
    'name': 'Notification',
    'version': '1.0',
    'summary': 'Notification Website',
    'description': "",
    'depends': ['bus', 'mail', 'web_notify'],
    'data': [
        # 'views/mail_templates.xml',
        # 'static/src/xml/systray.xml',
    ],
    # 'qweb': [
    #     'static/src/xml/systray.xml',
    # ],
    'assets': {'web.assets_backend': ['ev_web_notification/static/src/scss/variables.scss',
                                      'ev_web_notification/static/src/js/systray/systray_activity_menu.js',
                                      'ev_web_notification/static/src/js/systray/mail_notification_manager.js',
                                      'ev_web_notification/static/src/js/portal_systray_activity_menu.js',
                                      'ev_web_notification/static/src/scss/systray.scss',
                                      ],
               'web.assets_qweb': [
                   'ev_web_notification/static/src/xml/systray.xml',
               ]
               },
}
