##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def clean_internal_number(self):
        # We also clean reference for compatibility with argentinian loc
        for rec in self:
            # if document type has a sequence then a new sequence must be
            # requested. Otherwise, we want to keep number introduced by user
            if rec._fields in ['document_sequence_id']:
                rec.update({'move_name': False,
                            'document_number': False})
            else:
                rec.update({'move_name': False})
