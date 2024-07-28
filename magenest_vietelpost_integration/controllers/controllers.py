# -*- coding: utf-8 -*-
# from odoo import http


# class IntegrateShipping(http.Controller):
#     @http.route('/integrate_shipping/integrate_shipping/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/integrate_shipping/integrate_shipping/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('integrate_shipping.listing', {
#             'root': '/integrate_shipping/integrate_shipping',
#             'objects': http.request.env['integrate_shipping.integrate_shipping'].search([]),
#         })

#     @http.route('/integrate_shipping/integrate_shipping/objects/<model("integrate_shipping.integrate_shipping"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('integrate_shipping.object', {
#             'object': obj
#         })
