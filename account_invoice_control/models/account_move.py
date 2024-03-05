##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api

class AccountMove(models.Model):

    _inherit = "account.move"

    restrict_edit_invoice = fields.Boolean(compute='_compute_restrict_edit_invoice')

    def _compute_restrict_edit_invoice(self):
        if self.env.user.has_group('account_invoice_control.group_restrict_edit_invoice'):
            self.restrict_edit_invoice = True
        else:
            self.restrict_edit_invoice = False
