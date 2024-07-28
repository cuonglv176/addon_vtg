from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import datetime
import json


class KsDashboardNinjaAdvance(models.Model):
    _inherit = "ks_dashboard_ninja.board"

    ks_croessel_speed = fields.Selection([('3000', '3 Seconds'),
                                          ('5000', '5 Seconds'),
                                          ('10000', '10 Seconds'),
                                          ('15000', '15 Seconds'),
                                          ('30000', '30 Seconds'),
                                          ('45000', '45 Seconds'),
                                          ('60000', '1 minute'),
                                          ], string="Slide Interval", default = '5000')

    def ks_fetch_item_data(self, rec, params={}):
         item = super(KsDashboardNinjaAdvance, self).ks_fetch_item_data(rec, params)

         item["ks_data_calculation_type"] = rec.ks_data_calculation_type
         item['ks_list_view_layout'] = rec.ks_list_view_layout

         return item

    def ks_export_item_data(self, rec):
        item = super(KsDashboardNinjaAdvance, self).ks_export_item_data(rec)

        item['ks_data_calculation_type'] = rec.ks_data_calculation_type
        item['ks_custom_query'] = rec.ks_custom_query
        item['ks_xlabels'] = rec.ks_xlabels
        item['ks_ylabels'] = rec.ks_ylabels
        item['ks_list_view_layout'] = rec.ks_list_view_layout
        item['ks_is_date_ranges'] = rec.ks_is_date_ranges
        item['ks_query_start_date'] = rec.ks_query_start_date.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) if rec.ks_query_start_date else False
        item['ks_query_end_date'] = rec.ks_query_end_date.strftime(
                DEFAULT_SERVER_DATETIME_FORMAT) if rec.ks_query_end_date else False

        return item

    @api.model
    def ks_fetch_dashboard_data(self,ks_dashboard_id, ks_item_domain=False):
        dashboard_data = super(KsDashboardNinjaAdvance, self).ks_fetch_dashboard_data(ks_dashboard_id, ks_item_domain)
        dashboard_data['ks_croessel_speed'] = self.browse(ks_dashboard_id).ks_croessel_speed

        return dashboard_data

    def ks_create_item(self, item):
        if item.get('ks_data_calculation_type', False) == 'custom':
            model = self.env['ir.model'].search([('model', '=', item['ks_model_id'])])

            if not model and not item['ks_dashboard_item_type'] == 'ks_to_do':
                raise ValidationError(_(
                    "Please Install the Module which contains the following Model : %s " % item['ks_model_id']))


        ks_model_name = item['ks_model_id']

        ks_goal_lines = item['ks_goal_liness'].copy() if item.get('ks_goal_liness', False) else False
        ks_action_lines = item['ks_action_liness'].copy() if item.get('ks_action_liness', False) else False
        ks_dn_header_line = item['ks_dn_header_line'].copy() if item.get('ks_dn_header_line', False) else False
        ks_multiplier_lines = item['ks_multiplier_lines'].copy() if item.get('ks_multiplier_lines', False) else False

        # Creating dashboard items
        item = self.ks_prepare_item(item)

        if 'ks_goal_liness' in item:
            del item['ks_goal_liness']
        if 'ks_id' in item:
            del item['ks_id']
        if 'ks_action_liness' in item:
            del item['ks_action_liness']
        if 'ks_icon' in item:
            item['ks_icon_select'] = "Default"
            item['ks_icon'] = False
        if 'ks_dn_header_line' in item:
            del item['ks_dn_header_line']
        if 'ks_multiplier_lines' in item:
            del item['ks_multiplier_lines']


        ks_item = self.env['ks_dashboard_ninja.item'].create(item)

        if ks_goal_lines and len(ks_goal_lines) != 0:
            for line in ks_goal_lines:
                line['ks_goal_date'] = datetime.datetime.strptime(line['ks_goal_date'].split(" ")[0],
                                                                  '%Y-%m-%d')
                line['ks_dashboard_item'] = ks_item.id
                self.env['ks_dashboard_ninja.item_goal'].create(line)

        if ks_dn_header_line and len(ks_dn_header_line) != 0:
            for line in ks_dn_header_line:
                ks_line = {}
                ks_line['ks_to_do_header'] = line.get('ks_to_do_header')
                ks_line['ks_dn_item_id'] = ks_item.id
                ks_dn_header_id = self.env['ks_to.do.headers'].create(ks_line)
                if line.get(line.get('ks_to_do_header'), False):
                    for ks_task in line.get(line.get('ks_to_do_header')):
                        ks_task['ks_to_do_header_id'] = ks_dn_header_id.id
                        self.env['ks_to.do.description'].create(ks_task)

        if ks_action_lines and len(ks_action_lines) != 0:

            for line in ks_action_lines:
                if line['ks_sort_by_field']:
                    ks_sort_by_field = line['ks_sort_by_field']
                    ks_sort_record_id = self.env['ir.model.fields'].search(
                        [('model', '=', ks_model_name), ('name', '=', ks_sort_by_field)])
                    if ks_sort_record_id:
                        line['ks_sort_by_field'] = ks_sort_record_id.id
                    else:
                        line['ks_sort_by_field'] = False
                if line['ks_item_action_field']:
                    ks_item_action_field = line['ks_item_action_field']
                    ks_record_id = self.env['ir.model.fields'].search(
                        [('model', '=', ks_model_name), ('name', '=', ks_item_action_field)])
                    if ks_record_id:
                        line['ks_item_action_field'] = ks_record_id.id
                        line['ks_dashboard_item_id'] = ks_item.id
                        self.env['ks_dashboard_ninja.item_action'].create(line)
        if ks_multiplier_lines and len(ks_multiplier_lines) != 0:
            for rec in ks_multiplier_lines:
                ks_multiplier_field = rec['ks_multiplier_fields']
                ks_multiplier_field_id = self.env['ir.model.fields'].search([('model', '=', ks_model_name), ('id', '=', ks_multiplier_field)])
                if ks_multiplier_field:
                    rec['ks_multiplier_fields'] = ks_multiplier_field_id.id
                    rec['ks_dashboard_item_id'] = ks_item.id
                    self.env['ks_dashboard_item.multiplier'].create(rec)

        return ks_item

    @api.model
    def ks_import_dashboard(self, file, menu_id):
        try:
            # ks_dashboard_data = json.loads(file)
            ks_dashboard_file_read = json.loads(file)
        except:
            raise ValidationError(_("This file is not supported"))

        if 'ks_file_format' in ks_dashboard_file_read and ks_dashboard_file_read[
            'ks_file_format'] == 'ks_dashboard_ninja_export_file':
            ks_dashboard_data = ks_dashboard_file_read['ks_dashboard_data']
        else:
            raise ValidationError(_("Current Json File is not properly formatted according to Dashboard Ninja Model."))

        ks_dashboard_key = ['name', 'ks_dashboard_menu_name', 'ks_gridstack_config']
        ks_dashboard_item_key = ['ks_model_id', 'ks_chart_measure_field', 'ks_list_view_fields', 'ks_record_field',
                                 'ks_chart_relation_groupby', 'ks_id']

        # Fetching dashboard model info
        for data in ks_dashboard_data:
            if not all(key in data for key in ks_dashboard_key):
                raise ValidationError(
                    _("Current Json File is not properly formatted according to Dashboard Ninja Model."))
            ks_dashboard_top_menu_id = data.get('ks_dashboard_top_menu_id', False)
            if ks_dashboard_top_menu_id:
                try:
                    self.env['ir.ui.menu'].browse(ks_dashboard_top_menu_id).name
                    ks_dashboard_top_menu_id = self.env['ir.ui.menu'].browse(ks_dashboard_top_menu_id)
                except Exception:
                    ks_dashboard_top_menu_id = False

            vals = {
                'name': data['name'],
                'ks_dashboard_menu_name': data['ks_dashboard_menu_name'],
                'ks_dashboard_top_menu_id': menu_id.id if menu_id else self.env.ref("ks_dashboard_ninja.board_menu_root").id,
                'ks_dashboard_active': True,
                'ks_gridstack_config': data['ks_gridstack_config'],
                'ks_dashboard_default_template': self.env.ref("ks_dashboard_ninja.ks_blank").id,
                'ks_dashboard_group_access': False,
                'ks_set_interval': data['ks_set_interval'],
                'ks_date_filter_selection': data['ks_date_filter_selection'],
                'ks_dashboard_start_date': data['ks_dashboard_start_date'],
                'ks_dashboard_end_date': data['ks_dashboard_end_date'],
            }
            # Creating Dashboard
            dashboard_id = self.create(vals)

            if data['ks_gridstack_config']:
                ks_gridstack_config = eval(data['ks_gridstack_config'])
            ks_grid_stack_config = {}

            item_ids = []
            item_new_ids = []
            if data['ks_item_data']:
                # Fetching dashboard item info
                for item in data['ks_item_data']:
                    item['ks_company_id'] = False
                    if not all(key in item for key in ks_dashboard_item_key):
                        raise ValidationError(
                            _("Current Json File is not properly formatted according to Dashboard Ninja Model."))

                    # Creating dashboard items
                    item['ks_dashboard_ninja_board_id'] = dashboard_id.id
                    item_ids.append(item['ks_id'])
                    del item['ks_id']
                    ks_item = self.ks_create_item(item)
                    item_new_ids.append(ks_item.id)

            for id_index, id in enumerate(item_ids):
                if data['ks_gridstack_config'] and str(id) in ks_gridstack_config:
                    ks_grid_stack_config[str(item_new_ids[id_index])] = ks_gridstack_config[str(id)]

            self.browse(dashboard_id.id).write({
                'ks_gridstack_config': json.dumps(ks_grid_stack_config)
            })

        return "Success"
        # separate function to make item for import