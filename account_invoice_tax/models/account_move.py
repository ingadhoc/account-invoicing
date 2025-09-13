from odoo import models, fields, api


class AccountMove(models.Model):

    _inherit = "account.move"

    def _compute_tax_totals(self):
        for move in self:
            tax_context = {'inverse_invoice_currency_rate': move.inverse_invoice_currency_rate}
            for line in move.line_ids.filtered(lambda x: x.tax_fixed_amount_in_currency):
                #tax_context[line.tax_line_id.id] = line.tax_fixed_amount_in_currency
                tax_context[line.tax_line_id.id] = {
                    'fixed_amount':line.tax_fixed_amount_in_currency,
                    'rate': line.tax_fixed_amount / line.tax_fixed_amount_in_currency  
                }
            super(AccountMove, move.with_context(tax_context=tax_context))._compute_tax_totals()

    # def button_draft(self):
    #     for move in self:
    #         tax_context = {'inverse_invoice_currency_rate': move.inverse_invoice_currency_rate}
    #         for line in move.line_ids.filtered(lambda x: x.tax_fixed_amount_in_currency):
    #             tax_context[line.tax_line_id.id] = line.tax_fixed_amount_in_currency
    #         super(AccountMove, move.with_context(tax_context=tax_context)).button_draft()
