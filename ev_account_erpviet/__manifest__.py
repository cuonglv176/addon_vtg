# -*- coding: utf-8 -*-
{
    'name': "Account ERPVIET",

    'summary': """
        Account ERPVIET
        """,

    'description': """
        Account ERPVIET
    """,

    'author': "ERPVIET",
    'website': "http://www.erpviet.vn",

    'category': 'Accounting',
    'version': '0.1',

    'depends': ['account', 'account_accountant', 'account_asset'],

    # always loaded
    'data': [
        'views/account_journal_general_views.xml',
        'security/ir.model.access.csv',
        'views/account_fiscal_month_view.xml',
        'views/object_cost.xml',
        'views/res_currency_view.xml',
        'views/account_cost_factor.xml',
        'views/account_account.xml',
        'views/account_expense_item_view.xml',
        'views/res_config_settings_view.xml',
        'views/account_move_view.xml',
        'views/account_transfer_model.xml',
        'views/account_asset.xml',
        'wizard/account_change_lock_date_view.xml'
    ],
}
