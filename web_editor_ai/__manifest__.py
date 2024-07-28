# -*- coding: utf-8 -*-

{
    'name': 'Odoo Editor AI',
    'summary': 'Integrate OpenAI API with Odoo Editor | ChatGPT, GPT, GPT-3, GPT-3.5, GPT-4',
    'description': "A range of AI tools that you can access directly within Odoo Editor's Powerbox commands",
    'category': 'Productivity',
    'author': 'Omicron Odoo',
    'version': '2.1',
    'price': 149.90,
    'depends': [
        'base_setup', 'web_editor',
    ],
    'data': [
        "security/ir.model.access.csv",
        "data/content_generator_options.xml",
        'views/res_config_settings_views.xml',
        'views/content_generator_options_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web_editor.assets_wysiwyg': [
            'web_editor_ai/static/src/js/ai_dialog.js',
            'web_editor_ai/static/src/js/content_generator.js',
            'web_editor_ai/static/src/js/wysiwyg.js',

        ],
        'web.assets_backend': [
            'web_editor_ai/static/src/xml/web_editor_ai_templates.xml',
        ]
    },
    'external_dependencies': {
        'python': ['openai']
    },
    'images': ['static/description/main_screenshot.png'],
}
