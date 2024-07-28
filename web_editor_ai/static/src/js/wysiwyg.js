/** @odoo-module **/

// const Wysiwyg = require('web_editor.wysiwyg');
import {_t} from 'web.core';
import {OdooEditor} from '@web_editor/../lib/odoo-editor/src/OdooEditor';

const OdooEditorLib = require('@web_editor/../lib/odoo-editor/src/OdooEditor');
const preserveCursor = OdooEditorLib.preserveCursor;
const AiDialog = require('wysiwyg.widgets.AiDialog');
const ContentGenerator = require('wysiwyg.widgets.ContentGenerator');
import {patch} from "@web/core/utils/patch";

const rpc = require('web.rpc');
const Dialog = require('web.Dialog');

patch(OdooEditor.prototype, "prototype patch", {
    _createCommandBar() {

        this.options.commands.push(
            {
                groupName: _t('OpenAI'),
                title: _t('Content Generator'),
                priority: 10,
                description: _t('Let AI to quickly generate content for you.'),
                fontawesome: 'fa-magic',
                callback: () => this._openContentGenerator('generate_content'),
            },
            {
                groupName: _t('OpenAI'),
                title: _t('Grammar correction'),
                priority: 10,
                description: _t('Fix mistakes in the selected text.'),
                fontawesome: 'fa-pencil',
                callback: async () => {
                    const selection = window.getSelection().toString()
                    if (selection !== undefined && selection.trim() !== '') {
                        const response = await this._makeAiRequest(selection, 'correct_text')
                        this.execCommand('insertHTML', response)
                    }
                },
            },
            {
                groupName: _t('OpenAI'),
                title: _t('Translation'),
                priority: 10,
                description: _t('Translate the selected text.'),
                fontawesome: 'fa-language',
                callback: async () => {
                    const selection = window.getSelection().toString()
                    if (selection !== undefined && selection.trim() !== '') {
                        const response = await this._makeAiRequest(selection, 'translate_text')
                        this.execCommand('insertHTML', response)
                    }
                },
            },
            {
                groupName: _t('OpenAI'),
                title: _t('Vanilla Promt'),
                priority: 10,
                description: _t('Ask AI anything.'),
                fontawesome: 'fa-question',
                callback: () => this._openAiRequestBox('vanilla_request'),
            },
        )

        this._super(...arguments);


    },
    /**
     * Insert the response from OpenAI request
     */
    _openAiRequestBox: function (method) {
        const restoreSelection = preserveCursor(this.document);
        const aidialog = new AiDialog(this, {}).open()

        aidialog.on('save', this, async data => {
            if (data) {
                const response = await this._makeAiRequest(data, method)
                await Promise.resolve().then(() => restoreSelection());
                this.execCommand('insertHTML', response)
            }
        })
    },

    /**
     * Insert the response from OpenAI request
     */
    _openContentGenerator: function (method) {
        const restoreSelection = preserveCursor(this.document);
        const generator_dialog = new ContentGenerator(this, {}).open()

        generator_dialog.on('save', this, async final_data => {
            let content = false
            const preview_content = generator_dialog.previewContent
            if (preview_content) {
                content = preview_content
            } else if (final_data) {
                content = await this._makeAiRequest(final_data, method)
            }

            if (content) {
                await Promise.resolve().then(() => restoreSelection());
                this.execCommand('insertHTML', content)
            }

        })
    },

    /**
     * Call the orm method to make the request to OpenAI API
     * @param input
     */
    _makeAiRequest: async function (input, method) {
        try {
            const aiResponse = await rpc.query({
                    model: "ai.api",
                    method: method,
                    args: [input]
                }
            );
            return aiResponse
        } catch (e) {
            Dialog.alert(this, e.message.data.message);
        }

    }
});
