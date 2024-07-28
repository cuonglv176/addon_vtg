/** @odoo-module alias=theme_prime.body_component */
import AbstractComponent from '@theme_prime/js/editor/components/abstract_component';
import { registry } from '@web/core/registry';

let BodyComponent = AbstractComponent.extend({
    template: 'theme_prime.body_component',
    xmlDependencies: AbstractComponent.prototype.xmlDependencies.concat(['/theme_prime/static/src/xml/editor/components/body_component.xml']),
    /**
     * @constructor
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.SelectionComponentValue = options.components.SelectionComponent || {};
        this.UiComponent = options.components.UiComponent || {};
        this.hasUiComponent = _.contains(_.keys(options.components), 'UiComponent');
        this.model = this.SelectionComponentValue.model || 'product.template';
        this.subModel = this.SelectionComponentValue.subModel || 'product.template';
    },
    _getDefaultFieldValue: function () {
        return {
            SelectionComponent: this.SelectionComponentValue,
            UiComponent: this.UiComponent,
        };
    },
    ComponentCurrentState: function () {
        let componentValue = {};
        _.each(this.allComponents, (component, name) => {
            componentValue[name] = this._getComponentState(name);
        });
        return componentValue;
    },
});

registry.category("theme_prime_components").add("BodyComponent", BodyComponent);
export default BodyComponent;