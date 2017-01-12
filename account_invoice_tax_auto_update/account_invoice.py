# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def button_reset_taxes(self):
        return super(AccountInvoice, self.with_context(
            constraint_update_taxes=True)).button_reset_taxes()

    @api.multi
    @api.constrains('invoice_line')
    def update_taxes(self):
        context = dict(self._context)
        if context.get('constraint_update_taxes'):
            return True
        self.with_context(constraint_update_taxes=True).button_reset_taxes()
