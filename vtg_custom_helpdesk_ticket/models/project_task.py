# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = "project.task"

    def write(self, vals):
        for task_id in self:
            res = super(ProjectTask, self).write(vals)
            partner_to = []
            for user_id in task_id.user_ids:
                partner_to.append(user_id.partner_id.id)
            self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
                                                               partner_to,
                                                               'Bạn được giao task:' + task_id.name, 'project.task',
                                                               task_id.id,
                                                               datetime.now())

            return res

    @api.model
    def create(self, vals):
        task_id = super(ProjectTask, self).create(vals)
        partner_to = []
        for user_id in task_id.user_ids:
            partner_to.append(user_id.partner_id.id)
        self.env['mail.message']._push_system_notification(self.env.user.partner_id.id, '',
                                                           partner_to,
                                                           'Bạn được giao task:' + task_id.name, 'project.task',
                                                           task_id.id,
                                                           datetime.now())

        return task_id
