from odoo import models, fields, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class AccountChangeLockDate(models.TransientModel):
    _name = "account.change.lock.date"
    _inherit = "account.change.lock.date"

    def change_lock_date_inherit(self):
        if self.user_has_groups('account.group_account_manager'):
            vals = {}
            if self.period_lock_date:
                vals['period_lock_date'] = self.period_lock_date + relativedelta(hours=7)
            else:
                vals['period_lock_date'] = False
            if self.fiscalyear_lock_date:
                vals['fiscalyear_lock_date'] = self.fiscalyear_lock_date + relativedelta(hours=7)
            else:
                vals['fiscalyear_lock_date'] = False
            if self.tax_lock_date:
                vals['tax_lock_date'] = self.tax_lock_date + relativedelta(hours=7)
            else:
                vals['tax_lock_date'] = False
            self.env.company.sudo().write(vals)
        else:
            raise UserError(_('Only Billing Administrators are allowed to change lock dates!'))
        return {'type': 'ir.actions.act_window_close'}
