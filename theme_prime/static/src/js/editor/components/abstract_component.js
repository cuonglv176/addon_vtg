/** @odoo-module alias=theme_prime.abstract_component */
import Widget from 'web.Widget';
import { _t } from 'web.core';
import { registry } from "@web/core/registry";
// My fu*king OWL :)
// Yes i know you're here to understand our system
// Light could be dream, light could be dream :)
var AbstractComponent = Widget.extend({
    xmlDependencies: [],
    custom_events: _.extend({}, Widget.prototype.custom_events, {
        tp_component_value_changed: '_onChangeComponentValue',
        tp_confirm_changes: '_onComponentConfirmChanges',
        tp_change_visibility: '_onChangeComponentVisibility',
    }),
    /**
     * @constructor
     * @param {Object} options: useful parameters such as productIDs, domain etc.
     */
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.setWidgetState(options);
    },
    /**
     * @override
     */
    start: function () {
        return this._super.apply(this, arguments).then( () => {
            return Promise.all(this._appendSubComponents());
        });
    },

    //--------------------------------------------------------------------------
    // Getters
    //--------------------------------------------------------------------------

    /**
     * @returns {string}
     */
    ComponentCurrentState: function () {
        return {};
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     * @returns {Promise}
     */
    _appendSubComponents: function (component) {
        // Don't initialize dependent components
        let componentNodes = component ? this.$("[data-field-name=" + component + "]") : this.$("[data-component]:not([data-dependency])");
        let allPromise = [Promise.resolve()];
        if (componentNodes.length) {
            this.allComponents = this.allComponents || {};
            let values = this._getDefaultFieldValue() || {};
            _.each(componentNodes, componentElement => {
                let $component = $(componentElement);
                let componentName = $component.attr('data-component');
                let fieldName = $component.attr('data-field-name');
                let optionsValue = $component.attr('data-options');
                let parentComponentName = $component.attr('data-dependency');
                let options = optionsValue ? JSON.parse(optionsValue) : {};
                let PrimeComponent = registry.category("theme_prime_components").get(componentName);
                // parentComponentName always be there in allComponents
                let componentObject = new PrimeComponent(this, _.extend({ fieldName: fieldName, parentComponent: this.allComponents[parentComponentName] || false}, values[fieldName], options));
                this.allComponents[fieldName] = componentObject;
                allPromise.push(componentObject.appendTo($component).then(() => {
                    let childComponent = this.$("[data-dependency=" + fieldName + "]").attr("data-field-name");
                    if (childComponent) {
                        return this._appendSubComponents(childComponent);
                    }
                }));
            });
        }
        return allPromise;
    },
    /**
     * Fetch records
     * @private
     * @param params {Object}
     * @returns {Promise}
     */
    async _fetchRecords(params) {
        let { routePath, fields, domain, model, limit, extras} = params;
        return await this._rpc({ route: routePath, params: { domain: domain, fields: fields, model: model, limit: limit || 20, extras: extras}});
    },
    /**
     * Filter unnecessary results form the state
     * @private
     * @param result {Object}
     * @returns {Object}
     */
    _filterResult: function (result) {
        return _.pick(result, (value, key, object) => { return _.contains(_.keys(this.allComponents), key) });
    },
    /**
     * Refresh component and keep old state
     * @private
     * @param result {Object}
     * @returns {Object}
     */
    _forceRefreshComponent: function (component) {
        let componentObject = this.allComponents[component];
        if (componentObject) {
            this.destroyedComponents[component] = componentObject;
            componentObject.destroy();
            this.allComponents = _.omit(this.allComponents, component);
            this._appendSubComponents(component);
        }
    },
    /**
     * Get list of components that are child of this component
     * @private
     * @param fieldName {String} Name of the field (Not component name)
     * @returns {Array}
     */
    _getDependentSubComponents: function (fieldName) {
        return _.compact(_.map(this.allComponents, (component) => {
            if (component.parentComponent && component.parentComponent.fieldName === fieldName) {
                return component;
            }
        }));
    },
    /**
     * Get component state from all component
     * @private
     * @param fieldName {String} Name of the field (Not component name)
     * @returns {Object}
     */
    _getComponentState: function (fieldName) {
        let componentObj = _.find(this.allComponents, function (value, key) { return key == fieldName; });
        return componentObj ? componentObj.ComponentCurrentState() : false;
    },
    /**
     * Get component state from all component
     * @private
     * @param fieldName {String} Name of the field (Not component name)
     * @returns {Object}
     */
    _getComponentByName: function (fieldName) {
        return _.find(this.allComponents, function (co, key) { return key === fieldName })
    },
    /**
     * Notify child that parent changed it's state
     * @private
     * @param fieldName {String} Name of the field (Not component name)
     * @param state {object} component state
     */
    _notifyParentComponentStateChange: function (fieldName, state) { },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Set default values.
     * @param options {Object}
     */
    setWidgetState: function (options) {
        this.options = options || {};
        this.fieldName = options.fieldName;
        this.parentComponent = options.parentComponent || {};
        this.componentEnable = options.componentEnable;
        this.isEnabled = true;
        if (this.componentEnable && this.parentComponent) {
            this.isEnabled = this.parentComponent.ComponentCurrentState() === options.componentEnable;
        }
        this.destroyedComponents = {};
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onChangeComponentValue: function (ev) {
        if (ev.data && ev.data.fieldName) {
            _.each(this._getDependentSubComponents(ev.data.fieldName), (component) => { component._notifyParentComponentStateChange(ev.data.fieldName, this._getComponentState(ev.data.fieldName)) });
        }
    },
    /**
     * @private
     */
    _onComponentConfirmChanges: function (ev) {
        if (ev.data && ev.data.fieldName) {
            _.each(this._getDependentSubComponents(ev.data.fieldName), (component) => { component._notifyParentComponentStateChange(ev.data.fieldName, this._getComponentState(ev.data.fieldName))});
        }
    },
    /**
     * @private
     * @param {OdooEvent} ev
     */
    _onChangeComponentVisibility: function (ev) {
        let { hideField, displayField } = ev.data;
        this.$("[data-field-name=" + hideField + "]").addClass('d-none');
        this.$("[data-field-name=" + displayField + "]").removeClass('d-none');
    },
});

export default AbstractComponent;