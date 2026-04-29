from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _get_tax_totals_summary(self, base_lines, currency, company, cash_rounding=None):
        res = super()._get_tax_totals_summary(base_lines, currency, company, cash_rounding=cash_rounding)
        # ``tax_context`` is injected by AccountMove._compute_tax_totals when
        # there are active tax overrides.  Structure:
        #   { tax_id (int): {'fixed_amount': float, 'rate': float}, ... }
        if tax_context := self.env.context.get("tax_context"):
            for tax_group in res.get("subtotals", [{}])[0].get("tax_groups", []):
                for involved_tax_id in tax_group.get("involved_tax_ids", []):
                    override = tax_context.get(involved_tax_id)
                    if not override:
                        continue
                    new_amount = override.get("fixed_amount", 0.0)
                    rate = override.get("rate", 1.0)
                    original_amount = tax_group.get("tax_amount", 0.0)
                    original_currency_amount = tax_group.get("tax_amount_currency", 0.0)
                    if not new_amount or new_amount == original_currency_amount:
                        continue
                    diff = new_amount - original_currency_amount
                    currency_diff = new_amount / rate - original_amount
                    tax_group.update(
                        {
                            "tax_amount": new_amount / rate,
                            "tax_amount_currency": new_amount,
                        }
                    )
                    res["tax_amount"] += currency_diff
                    res["total_amount"] += currency_diff
                    res["tax_amount_currency"] += diff
                    res["total_amount_currency"] += diff

        return res
