# -*- coding: utf-8 -*-
# Copyright 2022 IZI PT Solusi Usaha Mudah

from odoo import http
from odoo.http import request
import json

class DashboardWebsiteController(http.Controller):
    def make_error_response(self, status, error, error_descrip):
        return request.make_response(json.dumps({
            'data': {
                'error': error,
                'error_descrip': error_descrip,
            },
            'code': status,
        }, default=str), headers=[
            ('Content-Type', 'application/json'),
        ])

    def make_valid_response(self, body):
        return request.make_response(json.dumps({
            'data': body,
            'code': 200
        }, default=str), headers=[
            ('Content-Type', 'application/json'),
        ])
    
    @http.route('/izi/dashboard/<int:dashboard_id>/page', auth='public', type='http', website=True)
    def get_dashboard_page(self, dashboard_id, **kw):
        return request.render('izi_dashboard.dashboard_page', {
            'dashboard_id': dashboard_id,
            'access_token': kw.get('access_token'),
        })
    
    @http.route('/izi/dashboard/<int:dashboard_id>', auth='public', type='http')
    def get_dashboard(self, dashboard_id, **kw):
        # Get System Parameter
        access_token = request.env['ir.config_parameter'].sudo().get_param('izi_dashboard.access_token')
        if not access_token:
            return self.make_error_response(500, 'Error', 'Access Token is not set. Dashboard access is not allowed!')
        if kw.get('access_token') != access_token:
            return self.make_error_response(401, 'Unauthorized', 'Access Token is not valid')
        
        # Whitelist IP Address
        ip_address = request.httprequest.remote_addr
        whitelist_ip_addresses = request.env['ir.config_parameter'].sudo().get_param('izi_dashboard.whitelist_ip_addresses')
        if whitelist_ip_addresses:
            whitelist_ip_addresses = whitelist_ip_addresses.split(',')
            whitelist_ip_addresses = [ip.strip() for ip in whitelist_ip_addresses]
            if ip_address not in whitelist_ip_addresses:
                return self.make_error_response(401, 'Unauthorized', 'IP Address is not allowed')
        
        if not dashboard_id:
            return self.make_error_response(500, 'Error', 'Dashboard ID is required')
        dashboard = request.env['izi.dashboard'].sudo().browse(dashboard_id)
        # Search Read Dashboard Block By Dashboard Id
        blocks = request.env['izi.dashboard.block'].sudo().search_read(
            domain=[['dashboard_id', '=', dashboard_id]],
            fields=['id', 'gs_x', 'gs_y', 'gs_w', 'gs_h', 'min_gs_w', 'min_gs_h', 'analysis_id', 'animation', 'refresh_interval', 'visual_type_name', 'rtl'],
        )
        data = {
            'theme_name': dashboard.theme_name,
            'blocks': blocks,
        }
        return self.make_valid_response(data)

    @http.route('/izi/analysis/<int:analysis_id>/data', auth='public', type='http')
    def get_analysis_data(self, analysis_id, **kw):
        # Get System Parameter
        access_token = request.env['ir.config_parameter'].sudo().get_param('izi_dashboard.access_token')
        if not access_token:
            return self.make_error_response(500, 'Error', 'Access Token is not set. Dashboard access is not allowed!')
        if kw.get('access_token') != access_token:
            return self.make_error_response(401, 'Unauthorized', 'Access Token is not valid')
        
        # Whitelist IP Address
        ip_address = request.httprequest.remote_addr
        whitelist_ip_addresses = request.env['ir.config_parameter'].sudo().get_param('izi_dashboard.whitelist_ip_addresses')
        if whitelist_ip_addresses:
            whitelist_ip_addresses = whitelist_ip_addresses.split(',')
            whitelist_ip_addresses = [ip.strip() for ip in whitelist_ip_addresses]
            if ip_address not in whitelist_ip_addresses:
                return self.make_error_response(401, 'Unauthorized', 'IP Address is not allowed')
        
        if not analysis_id:
            return self.make_error_response(500, 'Error', 'Analysis ID is required')
        analysis = request.env['izi.analysis'].sudo().browse(analysis_id)
        if not analysis:
            return self.make_error_response(500, 'Error', 'Analysis not found')
        result = analysis.get_analysis_data_dashboard(**kw.get('kwargs', {}))
        return self.make_valid_response(result)