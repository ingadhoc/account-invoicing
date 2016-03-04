# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models, api


class account_analytic_account(models.Model):

    _inherit = 'account.analytic.account'

    different_currency_id = fields.Many2one(
        'res.currency',
        'Invoice in different Currency?',
        help='If you want the invoice in a different currency from the'
        'contract, please select a currency'
    )

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        self.different_currency_id = False
        if self.pricelist_id.invoice_in_different_currency_id:
            self.different_currency_id = self.pricelist_id.invoice_in_different_currency_id.id


    def _prepare_invoice_data(self, cr, uid, contract, context=None):
        res = super(account_analytic_account, self)._prepare_invoice_data(
            cr, uid, contract, context=context)

        if contract.different_currency_id:
            if contract.pricelist_id.currency_id:
                price_currency_id = contract.pricelist_id.currency_id.id
            else:
                price_currency_id = self.pool['res.users'].browse(
                    cr, uid, uid).company_id.currency_id.id
            res['currency_id'] = contract.different_currency_id.id
            invoice_currency_rate = self.pool['res.currency'].compute(
                cr, uid, price_currency_id,
                contract.different_currency_id.id,
                1.0, round=False, context=context)
            res['invoice_currency_rate'] = invoice_currency_rate
        return res

    def _prepare_invoice_line(self, cr, uid, line, fiscal_position, context=None):
        res = super(account_analytic_account, self)._prepare_invoice_line(
            cr, uid, line, fiscal_position, context)
        if line.analytic_account_id.different_currency_id:
            if line.analytic_account_id.pricelist_id.currency_id:
                price_currency_id = line.analytic_account_id.pricelist_id.currency_id.id
            else:
                price_currency_id = self.pool['res.users'].browse(
                    cr, uid, uid).company_id.currency_id.id
            new_price_unit = self.pool['res.currency'].compute(
                cr, uid, price_currency_id,
                line.analytic_account_id.different_currency_id.id,
                res['price_unit'], round=False, context=context)
            res['price_unit'] = new_price_unit
        return res
