odoo.define('wysiwyg.widgets.AiDialog', function (require) {
'use strict';

var core = require('web.core');
var Dialog = require('wysiwyg.widgets.Dialog');
var _t = core._t;


var AiDialog = Dialog.extend({
    template: 'web_editor_ai.request_dialog',
    xmlDependencies: Dialog.prototype.xmlDependencies.concat(
        ['/web_editor_ai/static/src/xml/web_editor_ai_templates.xml']
    ),

    init: function (parent, options) {
        options = options || {};
        this._super(parent, _.extend({}, {
            title: _t("OpenAI request")
        }, options));


    },

    save: function () {

        this.final_data = this.$('#aiRequestInput').val();

        return this._super.apply(this, arguments);
    },

});


return AiDialog;
});
