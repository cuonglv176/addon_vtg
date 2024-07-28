# -*- coding: utf-8 -*-
import json
import logging
from odoo import http
from odoo.http import request, JsonRequest, Response
from odoo.tools import ustr, consteq, frozendict, pycompat, unique, date_utils


_logger = logging.getLogger(__name__)

status_mapping = {
    '1': 'new',
    '2': 'check',
    '3': 'sent',
    '4': 'delivery',
    '5': 'delivery',
    '7': 'successful',
    '8': 'return',
    '9': 'cancel',
    '13': 'return',
}


def _json_response(self, result=None, error=None):
    response = {
        'jsonrpc': '2.0',
        'id': self.jsonrequest.get('id')
    }
    if error is not None:
        response['error'] = error
    if result is not None:
        if type(result) == dict and 'ems' in result and result.get('ems'):
            result.pop('ems')
            response = result
        else:
            response['result'] = result

    mime = 'application/json'
    body = json.dumps(response, default=date_utils.json_default)

    return Response(
        body, status=error and error.pop('http_status', 200) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )
JsonRequest._json_response = _json_response


class VtgEmsShipping(http.Controller):

    # Content-Type : application/json
    # ems-transaction : [-transaction id-]
    # body: {
    #  "tracking_code": "EJ012345678VN",
    #  "order_code": "OD-123456",
    #  "status_code": 4,
    #  "status_name": "Đang vận chuyển",
    #  "note": "Ghi chú trạng thái",
    #  "locate": "Ba Đình, Hà Nội",
    #  "datetime": "31/10/2018 16:45:44",
    #  "total_weight" : 100
    # }

    # transfer_status: [
    #     {
    #         "code": 1, - new
    #         "name": "Đã tạo"
    #     },
    #     {
    #         "code": 2, - check
    #         "name": "Chờ lấy hàng"
    #     },
    #     {
    #         "code": 3, - sent
    #         "name": "Đã lấy hàng"
    #     },
    #     {
    #         "code": 4, - delivery
    #         "name": "Đang vận chuyển"
    #     },
    #     {
    #         "code": 5, - delivery
    #         "name": "Đang phát hàng"
    #     },
    #     {
    #         "code": 6, -
    #         "name": "Phát không thành công"
    #     },
    #     {
    #         "code": 7, - successful
    #         "name": "Phát thành công"
    #     },
    #     {
    #         "code": 8, - return
    #         "name": "Chuyển Hoàn"
    #     },
    #     {
    #         "code": 9, - cancel
    #         "name": "Đơn Hàng Hủy"
    #     },
    #     {
    #         "code": 12,
    #         "name": "Trạng thái khác"
    #     },
    #     {
    #         "code": 13,- return
    #         "name": "Phát hoàn thành công"
    #     }
    # ]

    @http.route(route='/vtg/ems/update_status', type='json', auth='public', methods=['POST'])
    def action_update_status(self, **kwargs):
        try:
            body = json.loads(request.httprequest.data)
            _logger.info('Create stores body: %s', body)
            tracking_code = body.get('tracking_code', '')
            order_id = request.env['sale.order'].sudo().search([('transfer_code', '=', tracking_code)])
            if order_id:
                status_transfer = status_mapping.get(str(body.get('status_code', 0)), '')
                if status_transfer:
                    order_id.status_transfer = status_transfer
        except:
            return {
                "ems": True,
                "code": "error",
                "transaction": request.httprequest.headers['ems-transaction']
            }
        return {
            "ems": True,
            "code": "success",
            "transaction": request.httprequest.headers['ems-transaction']
        }
