# -*- coding: utf-8 -*-
from odoo import api, Command, fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


OPTION_TYPES = [
    ('length', _('Length')),
    ('tone', _('Tone')),
    ('format', _('Format')),
]


class ContentGeneratorOptions(models.Model):
    _name = 'content.generator.options'
    _description = 'Content Generator Option'
    _order = 'type, sequence'

    sequence = fields.Integer(default=10)
    name = fields.Char('Description', required=True, translate=True)
    code = fields.Char('Description', compute='_compute_code', store=True)
    type = fields.Selection(OPTION_TYPES, default=OPTION_TYPES[0][0], required=True)

    @api.depends('name', 'type')
    def _compute_code(self):
        for record in self.filtered(lambda x: x.name):
            code = record.name.lower().replace(' ', '').strip()
            record.code = f'{record.type}_{code}'

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if record.code and self.search_count([('code', '=', record.code)]) > 1:
                raise ValidationError(_("An option with the name %s already exists") % record.name)

    @api.model
    def get_options(self, context=False):
        options = self.search([]).sorted(lambda o: o.sequence)
        option_dict = {}
        for option in options:
            op = (option.code, option.name, option.with_context(lang='en_US').name)
            if option.type in option_dict:
                option_dict[option.type].append(op)
            else:
                option_dict[option.type] = [op]

        for option_list in option_dict.values():
            option_list.append(('other', _('Other'), 'Other'))

        if isinstance(context, dict) and context.get('model') and context.get('id'):
            option_dict['about'] = [self._get_record_context(context)]

        return option_dict


    @api.model
    def _get_record_context(self, context):
        _logger.info(context)
        rec_model = context.get('model')
        rec_id = int(context.get('id'))
        record = self.env[rec_model].with_context(lang='en_US').browse(rec_id)

        additional_context = ''
        # record name
        if hasattr(record, 'name') and record.name:
            label = record._fields['name'].string
            additional_context += f"{label}: {record.name}"


        # product related context
        if rec_model in ['product.product', 'product.template']:
            if record.categ_id:
                additional_context += f'\nProduct category: {record.categ_id.name}'

            if rec_model == 'product.template':
                attribute_lines = record.attribute_line_ids

                if attribute_lines:
                    additional_context += '\nAvailable variants: '
                    for line in attribute_lines:
                        attribute = line.attribute_id.name
                        values = line.value_ids.mapped('name')

                        additional_context += f"\n{attribute}: {', '.join(values)}"

            elif rec_model == 'product.product':
                attributes = record.product_template_attribute_value_ids.mapped('display_name')
                additional_context += f"\nAttributes: {'; '.join(attributes)}"

            if record.list_price:
                additional_context += f"\nPrice: {record.list_price} {record.currency_id.name}"
        else:

            # partner info
            if hasattr(record, 'partner_id') and record.partner_id:
                label = record._fields['partner_id'].string
                additional_context += f"\n{label}: {record.partner_id.display_name}"
            # user info
            if hasattr(record, 'user_id') and record.user_id:
                label = record._fields['user_id'].string
                additional_context += f"\n{label}: {record.user_id.display_name}"
            # company info
            if hasattr(record, 'company_id') and record.company_id:
                label = record._fields['company_id'].string
                additional_context += f"\n{label}: {record.company_id.display_name}"






        return additional_context