# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Odoo Multi Vendor Marketplace",
  "summary"              :  """Start your marketplace in odoo with Odoo Multi-Vendor Marketplace. Allow        Multiple sellers to sell their products on your marketplace website.""",
  "category"             :  "Website",
  "version"              :  "1.0.1",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Multi-Vendor-Marketplace.html",
  "description"          :  """Odoo Multi Vendor Marketplace
        Sell on marketplace
        Register sellers on marketplace
        Marketplace in Odoo
        Odoo Marketplace website
        E-commerce marketplace
        Multi-Seller Marketplace
        Set up your Own Marketplace in Odoo website
        Multi vendor Marketplace in Odoo
        Multi-Vendor Marketplace in Odoo
        Sellers marketplace in Odoo
        Turn your Odoo website in Marketplace
        How to set up seller Marketplace in Odoo
        start marketplace in Odoo
        add multiple sellers""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=odoo_marketplace&lifetime=120&lout=1&custom_url=/",
  "depends"              :  [
                             'website_sale',
                             'stock_account',
                             'delivery',
                            ],
  "data"                 :  [
                             'security/marketplace_security.xml',
                             'edi/product_status_change_mail_to_admin.xml',
                             'edi/product_status_change_mail_to_seller.xml',
                             'edi/seller_creation_mail_to_admin.xml',
                             'edi/seller_creation_mail_to_seller.xml',
                             'edi/seller_status_change_mail_to_admin.xml',
                             'edi/seller_status_change_mail_to_seller.xml',
                             'edi/order_mail_to_seller.xml',
                             'data/mp_product_demo_data.xml',
                             'data/mp_config_setting_data.xml',
                             'data/seller_payment_method_data.xml',
                             'data/ir_config_parameter_data.xml',
                             'security/ir.model.access.csv',
                             'views/mp_backend_asset.xml',
                             'wizard/server_action_wizard.xml',
                             'wizard/seller_status_reason_wizard_view.xml',
                             'wizard/seller_payment_wizard_view.xml',
                             'wizard/seller_registration_wizard_view.xml',
                             'wizard/variant_approval_wizard_view.xml',
                             'views/sequence_view.xml',
                             'views/res_config_view.xml',
                             'views/website_config_view.xml',
                             'views/seller_shop_view.xml',
                             'views/res_partner_view.xml',
                             'views/seller_payment_view.xml',
                             'views/mp_stock_view.xml',
                             'views/seller_view.xml',
                             'views/mp_product_view.xml',
                             'views/mp_sol_view.xml',
                             'views/account_invoice_view.xml',
                             'views/seller_review_view.xml',
                             'views/website_mp_product_template.xml',
                             'views/website_mp_template.xml',
                             'views/website_seller_profile_template.xml',
                             'views/website_seller_shop_template.xml',
                             'views/website_account_template.xml',
                             'views/snippets/sell_snippets.xml',
                             'views/mp_menu_view.xml',
                             'data/marketplace_dashboard_demo.xml',
                             'data/seller_shop_style_data.xml',
                             'data/social_media_data.xml',
                             'views/mp_dashboard_view.xml',
                             'data/website_menus_data.xml',
                            ],
  "assets"              :  {
    "web.assets_backend" :  [
      'odoo_marketplace/static/src/css/mp_dashboard.css',
      'odoo_marketplace/static/src/js/kanban_column.js',
      'odoo_marketplace/static/src/js/url_handler.js'
    ],
    "web.assets_frontend" : [
      'odoo_marketplace/static/src/css/marketplace.css',
      'odoo_marketplace/static/src/css/marketplace_snippet.css',
      'odoo_marketplace/static/src/css/star-rating.css',
      'odoo_marketplace/static/src/css/review_chatter.scss',
      'odoo_marketplace/static/src/js/review_chatter.js',
      'odoo_marketplace/static/src/js/bootstrap-rating-input.min.js',
      'odoo_marketplace/static/src/js/star-rating.js',
      'odoo_marketplace/static/src/js/jquery.timeago.js',
      'odoo_marketplace/static/src/js/jquery.circlechart.js',
      'odoo_marketplace/static/src/js/seller_ratting.js',
      'odoo_marketplace/static/src/js/marketplace_snippets.js',
      'odoo_marketplace/static/src/js/marketplace.js'

    ]
  },
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  299,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
