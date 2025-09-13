from odoo import models, fields, api

class AccountTax(models.Model):

    _inherit = "account.tax"

    @api.model
    def _get_tax_totals_summary(self, base_lines, currency, company, cash_rounding=None):
        res = super()._get_tax_totals_summary(base_lines, currency, company, cash_rounding=cash_rounding)
        if 'tax_context' in self.env.context:
            rate = self.env.context.get('inverse_invoice_currency_rate', 1)
            for tax_groups in res['subtotals'][0]['tax_groups']:
                for involved_tax_id in tax_groups['involved_tax_ids']:
                    amount = self.env.context['tax_context'].get(involved_tax_id, {}).get('fixed_amount', 0.0)
                    rate = self.env.context['tax_context'].get(involved_tax_id, {}).get('rate', 1.0)
                    original_amount = tax_groups.get('tax_amount', {})
                    if amount and amount != original_amount:
                        tax_groups.update({
                            'tax_amount': amount,
                            'tax_amount_currency': amount
                        })
                        res['tax_amount'] += amount - original_amount
                        res['total_amount'] += amount - original_amount
                        res['tax_amount_currency'] += (amount - original_amount) * rate
                        res['total_amount_currency'] += (amount - original_amount) * rate

        return res
