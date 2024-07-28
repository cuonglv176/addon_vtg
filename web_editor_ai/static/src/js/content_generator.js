odoo.define('wysiwyg.widgets.ContentGenerator', function (require) {
'use strict';

var core = require('web.core');
var Dialog = require('wysiwyg.widgets.Dialog');
var AlertDialog = require('web.Dialog');
const rpc = require('web.rpc');
var _t = core._t;


var ContentGenerator = Dialog.extend({
    template: 'web_editor_ai.content_generator',
    xmlDependencies: Dialog.prototype.xmlDependencies.concat(
        ['/web_editor_ai/static/src/xml/web_editor_ai_templates.xml']
    ),


    init: function (parent, options) {
        options = options || {};
        this._super(parent, _.extend({}, {
            title: _t("Generate Content"),
            buttons: [{
                    text: _t("Save"),
                    classes: 'btn-primary',
                    click: this.save,
                },
                {
                    text: _t("Preview"),
                    close: false,
                    click: this.preview,
                },
                {
                    text: _t("Discard"),
                    close: true,
                },
                ]
        }, options));

        this.tone_options = ['Professional', 'Informational', 'Casual', 'Creative', 'Other']
        this.format_options = ['Article', 'Email', 'Product description', 'List', 'Other']
        this.length_options = []
        this.about = ''

        this.previewContent = false;
        this.context = {}

    },

    willStart: async function () {
        this._super();

        const params = new URLSearchParams(window.location.hash);
        this.context = {
            'model': params.get('model'),
            'id': params.get('#id')
        }

        const generatorOptions = await this._getOptions();

        this.length_options = generatorOptions['length']
        this.tone_options = generatorOptions['tone']
        this.format_options = generatorOptions['format']
        this.about = generatorOptions['about']




    },

    save: function () {
        this._setFinalData()
        if (this._checkRequiredFields()) {
            return this._super.apply(this, arguments);
        }
    },

    preview: async function () {
        this._setFinalData()
        if (this._checkRequiredFields()) {
            this.previewContent = await this._getPreviewContent()
            if (this.previewContent) {
                this.$('#previewContainer').removeClass('d-none')
                this.$('#previewContent').html(this.previewContent)
            }

        }
    },

    _setFinalData: function (){
        this.final_data = {
            about: this.$('#writeAbout').val(),
            tone: this.$("input[name='tone']:checked").val(),
            format: this.$("input[name='format']:checked").val(),
            length: this.$("input[name='length']:checked").val(),
        };
    },

    _getPreviewContent: async function () {
        try {
            const aiResponse = await rpc.query({
                    model: "ai.api",
                    method: 'generate_content',
                    args: [this.final_data]
                }
            );
            return aiResponse
        } catch (e) {
            AlertDialog.alert(this, e.message.data.message);
        }
    },

    _checkRequiredFields: function (){
        if (this.final_data.about) {
            return true
        } else {
            AlertDialog.alert(this, _t("AI needs to know what to write about!"));
            return false
        }
    },

    _getOptions: async function () {
        const options = await rpc.query({
                model: "content.generator.options",
                method: 'get_options',
                args: [this.context]
            }
        );

        return options
    },

});


return ContentGenerator;
});
