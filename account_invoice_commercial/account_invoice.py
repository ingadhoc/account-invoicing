# -*- coding: utf-8 -*-
from openerp import models, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.onchange('partner_id')
    def _onchange_partner_commercial(self):
        if self.partner_id.user_id:
            self.user_id = self.partner_id.user_id.id
