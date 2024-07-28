/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : https://store.webkul.com/license.html/ */
odoo.define('odoo_marketplace.marketplace_snippets', function (require) {

    var publicWidget = require('web.public.widget');
    publicWidget.registry.wkMarketplaceSnippets = publicWidget.Widget.extend({
        selector: '#open_store_button',

        start: function () {
            $this = this
            $this._fetch().then(function(result){$this.$el.html(result)});
            return this._super.apply(this, arguments);
        },
        _fetch: function () {
            return this._rpc({
                route: '/add/header/button',
            }).then(res => {
                var btn_content = 'Open a New Store';
                if (res == '/my/marketplace'){
                    btn_content = 'Go to Marketplace Dashboard';
                }
                var store_btn_el = `<a href="${res}" class="btn" style="font-weight:600;background:#3BD3F4;border-radius: 2px;color:#fff;text-transform: uppercase;">${btn_content}</a>`;
                return store_btn_el;
            });
        },
    });
});