/** @odoo-module alias=droggol.product_serarch **/

import searchExports from '@website/snippets/s_searchbar/000';
import { Markup } from 'web.utils';
import { B2bMixin } from 'theme_prime.mixins';

let {searchBar} = searchExports;

searchBar.include(_.extend({}, B2bMixin, {
    init: function () {
        this._super.apply(this, arguments);
        this.advanceMode = odoo.dr_theme_config.json_product_search.advance_search;
        if (this.advanceMode) {
            this.xmlDependencies = ['/theme_prime/static/src/xml/frontend/search_autocomplete.xml'];
        }
    },

    async _fetch() {
        this.isB2bActive = this._isB2bModeEnabled();
        if (this.advanceMode) {
            this.searchType = 'droggol';
            const res = await this._rpc({
                route: '/website/dr_search',
                params: {
                    'term': this.$input.val(),
                    'max_nb_chars': Math.round(Math.max(this.autocompleteMinWidth, parseInt(this.$el.width())) * 0.22),
                    'options': this.options,
                }
            });
            this._markupRecords(res.products.results);
            this._markupRecords(res.categories.results);
            this._markupRecords(res.suggestions.results);
            this._markupRecords(res.autocomplete.results);
            if (res.global_match) {
                res.global_match['name'] = Markup(res.global_match['name'])
            }
            this.results = res || {};
            return res
        } else {
            return this._super.apply(this, arguments);
        }
    },

    _markupRecords: function (results) {
        const fieldNames = ['name', 'description', 'extra_link', 'detail', 'detail_strike', 'detail_extra'];
        results.forEach(record => {
            for (const fieldName of fieldNames) {
                if (record[fieldName]) {
                    if (typeof record[fieldName] === "object") {
                        for (const fieldKey of Object.keys(record[fieldName])) {
                            record[fieldName][fieldKey] = Markup(record[fieldName][fieldKey]);
                        }
                    } else {
                        record[fieldName] = Markup(record[fieldName]);
                    }
                }
            }
        });
    },

    _onKeydown: function (ev) {
        if (ev.which === $.ui.keyCode.DOWN) {
            ev.preventDefault();
            $('.dropdown-menu.show').find('> a.dropdown-item:first').focus();
        } else { this._super.apply(this, arguments); }
    },

}));

export default {
    searchBar: searchBar,
};
