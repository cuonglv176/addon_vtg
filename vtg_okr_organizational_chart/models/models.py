# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Yadhu K (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo import models, fields, api


class OrganizationalChart(models.Model):
    _name = 'okr.organizational.chart'
    _description = "OKR Organizational Chart"

    @api.model
    def get_employee_data(self, okr_id):
        parent_okr = self.env['dpt.okr.manager'].search([('id', '=', str(okr_id))])
        data = {
            'name': parent_okr.name,
            'title': self._get_position(parent_okr),
            'children': [],
            'office': self._get_image(parent_okr),
        }
        okr = self.env['dpt.okr.manager'].search([('parent_id', '=', parent_okr.id)])
        for okr_id in okr:
            data['children'].append(self.get_children(okr_id, 'middle-level'))

        return {'values': data}

    @api.model
    def get_children(self, okr, style=False):
        data = []
        okr_data = {'name': okr.name, 'title': self._get_position(okr), 'office': self._get_image(okr)}
        childrens = self.env['dpt.okr.manager'].search([('parent_id', '=', okr.id)])
        for child in childrens:
            sub_child = self.env['dpt.okr.manager'].search([('parent_id', '=', child.id)])
            next_style = self._get_style(style)
            if not sub_child:
                data.append({'name': child.name, 'title': self._get_position(child), 'className': next_style,
                             'office': self._get_image(child)})
            else:
                data.append(self.get_children(child, next_style))

        if childrens:
            okr_data['children'] = data
        if style:
            okr_data['className'] = style

        return okr_data

    def _get_style(self, last_style):
        if last_style == 'middle-level':
            return 'product-dept'
        if last_style == 'product-dept':
            return 'rd-dept'
        if last_style == 'rd-dept':
            return 'pipeline1'
        if last_style == 'pipeline1':
            return 'frontend1'

        return 'middle-level'

    def _get_image(self, okr):
        image_path = """<img src='/web/image/hr.employee.public/""" + str(okr.employee_id.id) + """/image_1024/' id='""" + str(
            okr.employee_id.id) + """'/>"""
        return image_path

    def _get_position(self, okr):
        if okr.employee_id.sudo().job_id:
            return okr.employee_id.sudo().job_id.name
        return ""
