# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class account_invoice_tax_wizard(models.TransientModel):
    _name = 'account.invoice.tax.wizard'
    _description = 'Account Invoice Tax Wizard'

    @api.model
    def _get_invoice(self):
        return self._context.get('active_id', False)

    tax_id = fields.Many2one('account.tax', 'Tax', required=True,)
    name = fields.Char(string='Tax Description', required=True)
    amount = fields.Float(
        string='Amount', digits=dp.get_precision('Account'), required=True)
    invoice_id = fields.Many2one(
        'account.invoice',
        'Invoice',
        default=_get_invoice)
    base = fields.Float(
        string='Base',
        digits=dp.get_precision('Account'),
        required=True)
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Analytic account')
    invoice_type = fields.Selection(
        related='invoice_id.type', string='Invoice Type')
    invoice_company_id = fields.Many2one(
        'res.company', string='Company',
        related='invoice_id.company_id')

    @api.onchange('invoice_id')
    def onchange_invoice(self):
        self.base = self.invoice_id.amount_untaxed

    @api.onchange('tax_id')
    def onchange_tax(self):
        res = self.tax_id.compute_all(self.base)
        self.name = res['taxes'] and res['taxes'][0]['name'] or False

    @api.onchange('base', 'tax_id')
    def onchange_base(self):
        res = self.tax_id.compute_all(self.base)
        self.amount = res['taxes'] and res['taxes'][0]['amount'] or False

    @api.multi
    def confirm(self):
        if not self.invoice_id or not self.tax_id:
            return False
        invoice = self.invoice_id
        val = {
            'invoice_id': invoice.id,
            'name': self.name,
            'manual': True,
            'base': self.base,
            'amount': self.amount,
        }
        res = self.tax_id.compute_all(self.base)
        tax = res['taxes'][0]
        val = {
            'invoice_id': invoice.id,
            'name': self.name,
            'tax_id': self.tax_id.id,
            'amount': self.amount,
            'manual': True,
            'sequence': 99,
            'account_analytic_id': self.account_analytic_id.id,
            'account_id': invoice.type in ('out_invoice', 'in_invoice') and (
                tax['account_id'] or False) or (
                tax['refund_account_id'] or False),
        }
        self.env['account.invoice.tax'].create(val)
