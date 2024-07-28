/** @odoo-module alias=theme_prime.boolean_component */
import AbstractComponent from '@theme_prime/js/editor/components/abstract_component';
import { registry } from '@web/core/registry';

let BooleanComponent = AbstractComponent.extend({
    template: 'theme_prime.boolean_component',
    xmlDependencies: AbstractComponent.prototype.xmlDependencies.concat(['/theme_prime/static/src/xml/editor/components/boolean_component.xml']),
    events: {
        'change .custom-control-input': '_onChange'
    },

    /**
     * @constructor
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.value = options.value;
        this.title = options.title || "Boolean";
        this.uid = _.uniqueId('tp-boolean-component-');
    },
    ComponentCurrentState: function () {
        return this.value;
    },
    _onChange: function (ev) {
        this.value = $(ev.currentTarget).prop('checked');
        this.trigger_up('tp_component_value_changed', { fieldName: this.fieldName, value: this.value });
    },

});

registry.category("theme_prime_components").add("BooleanComponent", BooleanComponent);
export default BooleanComponent;