# -*- coding: utf-8 -*-
import logging
from odoo import http,_
from odoo.http import request, Response

_logger = logging.getLogger(__name__)
API_URL_PREFIX = '/vtg'

status_mapping = {
    100: 'new',
    102: 'new',
    103: 'check',
    104: 'sent',
    105: 'sent',
    106: 'return',
    107: 'cancel',
    500: 'delivery',
    501: 'successful',
    502: 'return',
    503: 'cancel',
    505: 'return',
}

class ShippingControllers(http.Controller):

    def invalid_respone(self, status, message):
        # Response.status = str(status)
        return {
            "message": message,
            "status": status,
        }

    @http.route(route=API_URL_PREFIX + '/status_transfer', type='json', auth='public', methods=['POST'], website=True)
    def sale_order_status_transfer(self):
        data = http.request.jsonrequest.get('DATA')
        order_code = data.get('ORDER_NUMBER')
        so_id = request.env['sale.order'].sudo().search([('transfer_code', '=', order_code)])
        if not so_id:
            return self.invalid_respone(404, "It seems to be no action was specified")
        so_id.update({
            # 'status_transfer': status_mapping.get(data.get('ORDER_STATUS'), so_id.status_transfer),
            'viettel_post_status': str(data.get('STATUS_NAME'))
        })
        content = str(data)
        chatter_message = _('''<b> Lich sử vận chuyển: </b> %s <br/>
                                                 ''') % (
            content
        )

        so_id.message_post(body=chatter_message)
        return {
            "message": "Update Transfer sale order success",
            "sale_order_id": so_id.id,
            "status": 200
        }
