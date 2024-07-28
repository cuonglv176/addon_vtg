odoo.define('theme_prime.website.snippet.editor', function (require) {
'use strict';

require('website.snippet.editor');
const weSnippetEditor = require('web_editor.snippet.editor');
const { _lt } = require('web.core');

weSnippetEditor.SnippetsMenu.include({
    optionsTabStructure: [...weSnippetEditor.SnippetsMenu.prototype.optionsTabStructure, ['theme-prime-options', _lt("Theme Prime Options")]],
});

});
