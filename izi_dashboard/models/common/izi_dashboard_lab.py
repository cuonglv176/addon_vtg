from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import requests

class IZIDashboard(models.Model):
    _inherit = 'izi.dashboard'

    izi_lab_api_key = fields.Char('IZI Lab API Key', compute='_compute_izi_lab_api_key')
    izi_lab_url = fields.Char('IZI Lab URL', compute='_compute_izi_lab_api_key')
    base_url = fields.Char('Base URL', compute='_compute_izi_lab_api_key')
    izi_dashboard_access_token = fields.Char('IZI Dashboard Access Token', compute='_compute_izi_lab_api_key')

    def _compute_izi_lab_api_key(self):
        for rec in self:
            rec.izi_lab_api_key = self.env.user.company_id.izi_lab_api_key
            rec.izi_lab_url = self.env['ir.config_parameter'].sudo().get_param('izi_lab_url')
            rec.base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            rec.izi_dashboard_access_token = self.env['ir.config_parameter'].sudo().get_param('izi_dashboard.access_token')
    
    def action_get_lab_analysis_config(self, analysis_id, analysis_name):
        izi_lab_url = self.env['ir.config_parameter'].sudo().get_param('izi_lab_url')
        if not izi_lab_url:
            raise UserError(_('Please set IZI Lab URL in System Parameters.'))
        res = requests.post('''%s/lab/analysis/%s/config''' % (izi_lab_url, analysis_id), json={
            'name': analysis_name,
            'izi_lab_api_key': self.env.company.izi_lab_api_key,
        })
        res = res.json()
        if res.get('result') and res.get('result').get('config'):
            data = res.get('result').get('config')
            # Call izi.dashboard.config.wizard to create dashboard
            res = self.env['izi.dashboard.config.wizard'].create({
                'dashboard_id': self.id,
            }).process_wizard(data=data)
            if res.get('errors'):
                res = {
                    'message': res['errors'][0]['error'],
                    'status': 500,
                }
        else:
            res = res.get('result')
        return res