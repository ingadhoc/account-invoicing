# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    number = fields.Integer(compute='_compute_number', store=True)

    @api.multi
    @api.depends('sequence', 'invoice_id')
    def _compute_number(self):
        for invoice in self.mapped('invoice_id'):
            number = 1
            for line in invoice.invoice_line_ids:
                line.update({'number':number})
                number += 1
