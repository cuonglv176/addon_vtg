/** @odoo-module alias=theme_prime.range_component */
import AbstractComponent from '@theme_prime/js/editor/components/abstract_component';
import { registry } from '@web/core/registry';

let RangeComponent = AbstractComponent.extend({
    template: 'theme_prime.range_component',
    xmlDependencies: AbstractComponent.prototype.xmlDependencies.concat(['/theme_prime/static/src/xml/editor/components/range_component.xml']),
    events: {
        'input .tp-range-input': '_onInput',
        'change .tp-range-input': '_onChange'
    },

    /**
     * @constructor
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.maxValue = options.maxValue || 6;
        this.value = _.contains(_.keys(options), 'value') ? options.value : 4;
        this.minValue = _.contains(_.keys(options), 'minValue') ? options.minValue : 4;
        this.title = options.title;
    },
    ComponentCurrentState: function () {
        return this.value;
    },
    _onChange: function () {
        this.trigger_up('tp_component_value_changed', { fieldName: this.fieldName, value: parseInt(this.value) });
    },
    _onInput: function (ev) {
        let value = $(ev.currentTarget).val();
        this.$('.tp-current-count').html(value);
        this.value = value;
    },

});

registry.category("theme_prime_components").add("RangeComponent", RangeComponent);
export default RangeComponent;