# -*- coding: utf-8 -*-
from odoo import http, api, _
import logging
from addons_custom import status
import xmlrpc
import logging
import json
import werkzeug.wrappers
from odoo import http
from odoo.http import request, Response
import random
from datetime import datetime

ACCESS_TOKEN_LENGTH = 64

_logger = logging.getLogger(__name__)

default_password = ['122abd', '946gfk', 'fg890g', '236633', 'fa3311', '442288', 'asd887', 'qws545', '122gyg', '11qq11']

API_URL_PREFIX = '/vtg'


class ApiController(http.Controller):

    def invalid_respone(self, status, message):
        # Response.status = str(status)
        return {
            "message": message,
            "status": status,
        }

    def generate_access_token(self):
        my_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        return ''.join(random.choice(my_chars) for i in range(ACCESS_TOKEN_LENGTH))

    def _check_access_token(self, user, token):
        access_token = http.request.env['api.access_token'].sudo().search(
            [('user_id', '=', user.id), ('token', '=', token)], order='id DESC', limit=1)
        # if user and user.x_access_token:
        #     all_tokens = user.x_access_token
        #     list_token = all_tokens.split(";")
        #     # _logger.info(list_token)
        #     if token in list_token:
        #         return True
        if access_token:
            return True
        return False

    def _login(self, login, token):
        user = False
        if login and token:
            res_users = http.request.env['res.users'].sudo()
            user = res_users.search([('login', '=', login)])
            res_token = self._check_access_token(user, token)
            if res_token:
                return user
            else:
                return False
            # return {
            #     "message": "Access token is invalid",
            #     "status": status_PARAM_NOT_PROVIDED,
            # }
        return user

    @http.route(route=API_URL_PREFIX + '/login', type='json', auth='none', methods=['POST'], website=True)
    def login(self, **kwargs):
        return self.dispatch_request('login')

    def dispatch_request(self, action, **kw):
        # try:
        r = None
        if action == 'login':
            r = self.do_login()
        if r is not None:
            return r
        else:
            return self.invalid_respone(status.FOUND, "It seems to be no action was specified")

    def do_login(self):
        params = http.request.jsonrequest
        headers = http.request.httprequest.headers
        cr = http.request.cr
        if not params.get('login'):
            return self.invalid_respone(status.MISDIRECTED_REQUEST, "login MISDIRECTED REQUEST")
        if not params.get('password'):
            return self.invalid_respone(status.MISDIRECTED_REQUEST, "password MISDIRECTED REQUEST")
        login = params.get('login')
        password = params.get('password')
        if not password:
            return self.invalid_respone(status.UNAUTHORIZED, "Wrong password")
        _token = request.env['api.access_token']
        token_generate = self.generate_access_token()
        res_users = http.request.env['res.users']
        token_obj = http.request.env['api.access_token']
        user = res_users.sudo().search([('login', '=', login)])
        if user:
            token = token_obj.sudo().search([('user_id', '=', user.id)])
            if token:
                # token.sudo().write({
                # 	'token': token_generate,
                # })
                return {
                    "message": "Logged in successfully",
                    "login": user.login,
                    "name": user.name,
                    "token": token.token,
                    "user_id": user.id,
                    "status": 200,
                    "code": 1,
                }
            else:
                token = token_obj.sudo().create({
                    'user_id': user.id,
                    'scope': 'userinfo',
                    'token': token_generate,
                    # 'expires': datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                })
                return {
                    "message": "Logged in successfully",
                    "login": user.login,
                    "name": user.name,
                    "token": token.token,
                    "user_id": user.id,
                    "status": 200,
                    "code": 1,
                }
        else:
            return self.invalid_respone(status.UNAUTHORIZED, "Access_token FAILED")
