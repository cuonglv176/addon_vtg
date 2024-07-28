# -*- coding: utf-8 -*-
from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang
import openai
import logging

_logger = logging.getLogger(__name__)


class AiApi(models.Model):
    _name = 'ai.api'
    _description = 'OpenAI API'

    @api.model
    def make_ai_request(self, prompt):
        openai.api_key = self.env['ir.config_parameter'].sudo().get_param('web_editor_ai.api_key')
        model = self.env['ir.config_parameter'].sudo().get_param('web_editor_ai.model')

        try:
            response = openai.ChatCompletion.create(
                model=model,
                temperature=1,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as error:
            raise ValidationError(error)

    @api.model
    def correct_text(self, text):
        prompt = f'Check the text for grammar mistakes. Respond only with the revised text without any comments. The text is:\n{text}'
        return self.make_ai_request(prompt)

    @api.model
    def translate_text(self, text):
        language = get_lang(self.env).code
        prompt = f'Translate the provided text to {language}. Respond only with the translation. The text is:\n{text}'
        return self.make_ai_request(prompt)

    @api.model
    def generate_content(self, data):
        about = data.get('about', '')
        tone = data.get('tone', '')
        text_format = data.get('format', '')
        length = data.get('length', '')

        text_format = '' if text_format == 'Other' else f'Format: {text_format}.\n'
        tone = '' if tone == 'Other' else f'Tone: {tone}.\n'
        length = '' if length == 'Other' else f'Length: {length}.\n'

        prompt = f"""Create some content and format the response as HTML.
{text_format} {length} {tone}
The content is about:\n{about}
"""

        return self.make_ai_request(prompt)

    @api.model
    def vanilla_request(self, text):
        prompt = f'{text}\\n Format the response as HTML.'
        return self.make_ai_request(prompt)


