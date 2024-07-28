/** @odoo-module alias=theme_prime.dropdown_component */
import AbstractComponent from '@theme_prime/js/editor/components/abstract_component';
import { registry } from '@web/core/registry';
import { qweb, _t } from 'web.core';
const weWidgets = require('wysiwyg.widgets');

let DropDownComponent = AbstractComponent.extend({
    template: 'theme_prime.dropdown_component',
    xmlDependencies: AbstractComponent.prototype.xmlDependencies.concat(['/theme_prime/static/src/xml/editor/components/dropdown_component.xml']),
    events: {
        'click .dropdown-item': '_onClickOption'
    },

    /**
     * @constructor
     */
    init: function (parent, options) {
        this.uid = _.uniqueId('tp-dropdown-component-');
        this.records = options.records || [];
        this.recordID = options.recordID || false;
        this.buttonClasses = options.buttonClasses || 'btn-primary';
        this._super.apply(this, arguments);
    },

    _notifyParentComponentStateChange: function (fieldName, state) {
        this.isEnabled = this.componentEnable === state;
        this._refreshDropdown();
        this.$el.toggleClass('tp-disabled-component', !this.isEnabled);
    },
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @returns {Object} record
     */
    _getRecordByID: function (recordID) {
        return _.findWhere(this.records, { id: recordID });
    },
    /**
     * @private
     * @returns {Object} record
     */
    _widgetNotifyChanges: function (recordID) {
        this.recordID = recordID;
        this._refreshDropdown();
        this.trigger_up('tp_component_value_changed', {fieldName: this.fieldName, value: this.recordID});
    },
    /**
     * @private
     */
    _refreshDropdown: function () {
        var $placeholder = $(qweb.render('theme_prime.tp_dropdown_placeholder', {record: this._getRecordByID(this.recordID) }));
        var $items = $(qweb.render('theme_prime.dropdown_component_items', {widget:this, record: this._getRecordByID(this.recordID), records: this.records }));
        this.$('.tp-dropdown-placeholder').empty().append($placeholder);
        this.$('.tp-dropdown-menu').empty().append($items);
    },
    /**
     * @private
     */
    ComponentCurrentState: function () {
        return this._getRecordByID(this.recordID).id;
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
    * @private
    */
    _onClickOption: function (ev) {
        this._widgetNotifyChanges($(ev.currentTarget).attr('data-record-id'));
    },
});

let cardGrid = AbstractComponent.extend({
    template: 'theme_prime.cardGrid_component',
    xmlDependencies: AbstractComponent.prototype.xmlDependencies.concat(['/theme_prime/static/src/xml/editor/components/dropdown_component.xml']),
    /**
     * @constructor
     */
    init: function (parent, options) {
        this.records = options.records || [];
        this.recordsIDs = [];
        this._setRecordsState();
        this.stylesRegistry = registry.category('theme_prime_mega_menu_cards');
        this.styles = _.keys(this.stylesRegistry.content);
        this.activeRecordID = this.records.length ? this.records[0].id : false;
        this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    willStart: async function () {
        const res = this._super(...arguments);
        if (this.recordsIDs && this.recordsIDs.length) {
            this.fetchedCategoryData = await this._rpc({ route: '/theme_prime/get_categories_info', params: { options: { getCount: true, categoryIDs: this.recordsIDs }, fields: [] } });
        }
        return res;
    },
    /**
     * @private
     * @returns {object}
     */
    _getDefaultFieldValue: function () {
        let result = {};
        this.records.forEach(record => {
            result[`${record.id}_style`] = { recordID: record.style, records: _.map(this.styles, function (style, index) { return { id: style, title: _t(`Style - ${index + 1}`) }; })} || false;
            result[`${record.id}_productListing`] = { recordID: record.productListing, records: [{ id: 'bestseller', title: _t("Best Seller"), iconClass: 'dri dri-bolt' }, { iconClass: 'fa fa-percent', id: 'discount', title: _t("Discount") }]};
            result[`${record.id}_brand`] = { value: record.brand};
            result[`${record.id}_label`] = { value: record.label};
            result[`${record.id}_count`] = { value: record.count};
            result[`${record.id}_background`] = { value: record.background};
            result[`${record.id}_limit`] = { value: record.limit, maxValue: 21, minValue: 0 };
            result[`${record.id}_child`] = { value: record.child, maxValue: 21, minValue: 3 };
        });
        return result;
    },
    ComponentCurrentState: function () {
        let records = [];
        this.records.forEach(record => {
            records.push(_.pick(record, ['style', 'productListing', 'brand', 'label', 'count', 'id', 'limit', 'background', 'child']));
        });
        return {
            activeRecordID: this.activeRecordID,
            records: records,
        };
    },
    _getCount: function (categoryID) {
        let category = _.findWhere(this.fetchedCategoryData, { id: categoryID});
        return category ? category.count : false;
    },
    _setRecordsState: function () {
        this.records.forEach(record => {
            record['style'] = record.style || "s_tp_hierarchical_category_style_1";
            record['productListing'] = record.productListing || "bestseller";
            record['brand'] = record.brand || false;
            record['label'] = record.label || false;
            record['count'] = record.count || false;
            record['child'] = record.hasOwnProperty('child') ? record.child : 4;
            record['limit'] = record.hasOwnProperty('limit') ? record.limit : 4;
            record['background'] = record.background || false;
            this.recordsIDs.push(record.id);
        });
    },
    _updateRecordState: function (id, field, value) {
        this.records.forEach(record => {
            if (parseInt(id) === record.id) {
                record[field] = value;
                this.activeRecordID = record.id;
                this.$('.tp-category-card-component').removeClass('tp-active-card');
                this.$('.tp-category-card-component[data-category-id=' + this.activeRecordID + ']').addClass('tp-active-card');
            }
        });
    },
    /**
     * @private
     * @returns {Array}
     */
    _onChangeComponentValue: function (ev) {
        ev.stopPropagation();
        this._super.apply(this, arguments);
        let {fieldName, value} = ev.data;
        let categoryID = fieldName.split("_")[0];
        let field = fieldName.split("_")[1];
        this._updateRecordState(categoryID, field, value);
        this.getParent().trigger_up('tp_component_value_changed', { fieldName: this.fieldName, value: this.ComponentCurrentState() });
    },
});

let toggleButtonComponent = AbstractComponent.extend({
    template: 'theme_prime.toggleButtonComponent',
    events: {
        'click .tp-image-icon': '_onClickUploadImg',
        'click .tp-remove-image': '_onClickRemoveImg'
    },
    xmlDependencies: AbstractComponent.prototype.xmlDependencies.concat(['/theme_prime/static/src/xml/editor/components/dropdown_component.xml']),
    /**
     * @constructor
     */
    init: function (parent, options) {
        this.value = options.value || false;
        this.iconClass = options.iconClass || 'fa fa-camera';
        this.imageMode = options.imageMode || false;
        this.title = options.title || false;
        this._super.apply(this, arguments);
    },

    _refreshButton: function () {
        var $content = $(qweb.render('theme_prime.toggleButtonComponentContent', { widget: this }));
        this.$el.empty().append($content);
        this.trigger_up('tp_component_value_changed', { fieldName: this.fieldName, value: this.value });
    },
    _onClickUploadImg: function (ev) {
        if (this.imageMode) {
            var $image = $('<img/>');
            var mediaDialog = new weWidgets.MediaDialog(this, {onlyImages: true, res_model: 'ir.ui.view'}, $image[0]);
            mediaDialog.open();
            mediaDialog.on('save', this, function (image) {
                this.value = $(image).attr('src');
                this._refreshButton();
            });
        } else {
            this.value = !this.value;
            this._refreshButton();
        }
    },
    _onClickRemoveImg: function () {
        this.value = false;
        this._refreshButton();
    },
    ComponentCurrentState: function () {
        return this.value;
    }
});

registry.category("theme_prime_components").add("cardGrid", cardGrid);
registry.category("theme_prime_components").add("DropDownComponent", DropDownComponent);
registry.category("theme_prime_components").add("toggleButtonComponent", toggleButtonComponent);
export default { DropDownComponent, cardGrid, toggleButtonComponent};