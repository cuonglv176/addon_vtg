# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

{
    'name': 'Theme Prime',
    'description': 'Powerful multipurpose eCommerce theme suitable for all kind of businesses like Electronics, Fashion, Sports, Beauty, Furniture and many more.',
    'summary': 'Powerful multipurpose eCommerce theme suitable for all kind of businesses like Electronics, Fashion, Sports, Beauty, Furniture and many more.',
    'category': 'Theme/eCommerce',
    'version': '15.0.0.3.0',
    'depends': ['droggol_theme_common'],

    'license': 'OPL-1',
    'author': 'Droggol Infotech Private Limited',
    'company': 'Droggol Infotech Private Limited',
    'maintainer': 'Droggol Infotech Private Limited',
    'website': 'https://www.droggol.com/',

    'price': 289.00,
    'currency': 'USD',
    'live_test_url': 'https://prime-15-electronics-1.droggol.com/',

    'images': [
        'static/description/prime_cover.png',
        'static/description/prime_screenshot.gif',
    ],
    'data': [
        'data/theme.ir.attachment.csv',

        'views/templates.xml',
        'views/components.xml',
        'views/layout.xml',
        'views/pages.xml',
        'views/snippets.xml',
        'views/svg_images.xml',

        # Headers / Footers
        'views/headers.xml',
        'views/preheaders.xml',
        'views/footers.xml',

        # Snippets
        'views/snippets/dynamic_snippets.xml',
        'views/snippets/s_banner.xml',
        'views/snippets/s_blog.xml',
        'views/snippets/s_clients.xml',
        'views/snippets/s_coming_soon.xml',
        'views/snippets/s_countdown.xml',
        'views/snippets/s_cover.xml',
        'views/snippets/s_cta.xml',
        'views/snippets/s_gallery.xml',
        'views/snippets/s_heading.xml',
        'views/snippets/s_icon_block.xml',
        'views/snippets/s_info_block.xml',
        'views/snippets/s_pricing.xml',
        'views/snippets/s_shop_offer.xml',
        'views/snippets/s_stats.xml',
        'views/snippets/s_subscribe.xml',
        'views/snippets/s_team.xml',
        'views/snippets/s_testimonial.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Libraries
            'theme_prime/static/lib/OwlCarousel2-2.3.4/assets/owl.carousel.css',
            'theme_prime/static/lib/OwlCarousel2-2.3.4/assets/owl.theme.default.css',
            # Frontend
            'theme_prime/static/src/js/website.js',
            'theme_prime/static/src/js/website_sale.js',
            'theme_prime/static/src/js/website_sale_wishlist.js',
            'theme_prime/static/src/js/sidebar.js',
            'theme_prime/static/src/js/suggested_product_slider.js',
            'theme_prime/static/src/js/service_worker_register.js',
            'theme_prime/static/src/js/core/mixins.js',
            'theme_prime/static/src/js/frontend/comparison.js',
            'theme_prime/static/src/js/frontend/quick_view_dialog.js',
            'theme_prime/static/src/js/frontend/ajax_load_products.js',
            'theme_prime/static/src/js/frontend/bottombar.js',

            'theme_prime/static/src/scss/theme.scss',
            'theme_prime/static/src/scss/rtl.scss',
            'theme_prime/static/src/scss/website.scss',
            'theme_prime/static/src/scss/website_sale.scss',
            'theme_prime/static/src/scss/sliders.scss',
            'theme_prime/static/src/scss/icon-packs/website.scss',
            'theme_prime/static/src/scss/utils.scss',
            'theme_prime/static/src/scss/snippets/cards.scss',
            'theme_prime/static/src/scss/front_end/quick_view.scss',
            'theme_prime/static/src/scss/front_end/dynamic_snippets.scss',
            'theme_prime/static/src/scss/front_end/category_filters.scss',
            'theme_prime/static/src/scss/front_end/image_hotspot.scss',
            'theme_prime/static/src/scss/snippets/2_col_deal.scss',
            'theme_prime/static/src/scss/snippets/image_products.scss',
            'theme_prime/static/src/scss/front_end/bottom_bar.scss',
            # Core
            'theme_prime/static/src/js/core/snippet_root_widget.js',
            'theme_prime/static/src/js/core/product_root_widget.js',
            'theme_prime/static/src/js/core/cart_manager.js',
            'theme_prime/static/src/js/core/cart_confirmation_dialog.js',
            # Snippets
            'theme_prime/static/src/js/frontend/dynamic_snippets.js',
            # Editor
            ('replace', 'web_editor/static/src/scss/web_editor.frontend.scss', 'theme_prime/static/src/scss/web_editor.frontend.scss'),

            # Search
            'theme_prime/static/src/js/frontend/search.js',
        ],
        'web._assets_primary_variables': [
            'theme_prime/static/src/scss/primary_variables.scss',
            'theme_prime/static/src/scss/mixins.scss',
        ],
        'web._assets_frontend_helpers': [
            'theme_prime/static/src/scss/bootstrap_overridden.scss',
        ],
        'website.assets_wysiwyg': [
            'theme_prime/static/src/js/editor/snippets.editor.js',
            'theme_prime/static/src/scss/editor/editor.scss',
            'theme_prime/static/src/scss/editor/dialogs/dialog_snippet_configurator.scss',
            'theme_prime/static/src/scss/components/components.scss',
        ],
        'website.assets_editor': [
            'theme_prime/static/src/js/core/theme_config.js',
            'theme_prime/static/src/js/editor/snippet.options.js',
            # Widgets
            'theme_prime/static/src/js/editor/components/abstract_component.js',
            'theme_prime/static/src/js/editor/components/product_selection_component.js',
            'theme_prime/static/src/js/editor/components/dropdown_component.js',
            'theme_prime/static/src/js/editor/components/selection_component.js',
            'theme_prime/static/src/js/editor/components/body_component.js',
            'theme_prime/static/src/js/editor/components/ui_component.js',
            'theme_prime/static/src/js/editor/components/range_component.js',
            'theme_prime/static/src/js/editor/components/boolean_component.js',
            'theme_prime/static/src/js/editor/components/domain_component.js',
            'theme_prime/static/src/js/editor/registries.js',
            'theme_prime/static/src/js/editor/dialogs/dialog_snippet_configurator.js',
        ],
    },
}
