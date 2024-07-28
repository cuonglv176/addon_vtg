{
    'name': "VTG user custom",
    'name_vi_VN': "Tạo tài khoản cho đại lý",

    'summary': """
Synchronize sale contract to distributor
    """,
    'summary_vi_VN': """
      Tạo tài khoản cho đại lý    """,

    'description': """
What it does
============
Synchronize sale contract to distributor

Editions Supported
==================
1. Community Edition
2. Enterprise Edition

    """,

    'description_vi_VN': """
Ứng dụng này làm gì
===================
Tạo tài khoản cho đại lý

Ấn bản được Hỗ trợ
==================
1. Ấn bản Community
2. Ấn bản Enterprise

    """,

    'author': "cuonglv",
    'website': "https://hyundai.tcmotor.vn",
    'support': "cuonglv@hyundai.tcmotor.vn",
    'category': 'Other',
    'version': '0.1.0',
    'depends': ['mail','vtg_custom_lead','base','sale'],

    'data': [
        # 'security/ir.model.access.csv',
        # 'views/htv_create_user_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 99.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}
