from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _prepare_base_line_tax_repartition_grouping_key(
        self, base_line, base_line_grouping_key, tax_data, tax_rep_data
    ):
        """Never drop the tax line of a fixed tax on a vendor bill.

        The core removes every tax line whose amount nets to zero, which happens
        with a fixed tax set on a positive and a negative base line: the fixed
        amount follows the sign of ``price_unit``, so both cancel each other.
        The amount of those taxes is the one managed by this module, and
        ``AccountMove._apply_tax_overrides`` applies it by writing on the tax
        line.  Without a line there is nothing to write on, so the manual amount
        is silently lost from the entry while the totals widget still shows it.
        """
        res = super()._prepare_base_line_tax_repartition_grouping_key(
            base_line, base_line_grouping_key, tax_data, tax_rep_data
        )
        record = base_line.get("record")
        if (
            tax_data["tax"].amount_type == "fixed"
            and isinstance(record, models.Model)
            and record._name == "account.move.line"
            and record.move_id.move_type in ("in_invoice", "in_refund", "in_receipt")
        ):
            res["__keep_zero_line"] = True
        return res

    @api.model
    def _get_tax_totals_summary(self, base_lines, currency, company, cash_rounding=None):
        res = super()._get_tax_totals_summary(base_lines, currency, company, cash_rounding=cash_rounding)
        # ``tax_context`` is injected by AccountMove._compute_tax_totals when
        # there are active tax overrides.  Structure:
        #   { tax_id (int): {'fixed_amount': float, 'rate': float}, ... }
        if tax_context := self.env.context.get("tax_context"):
            original_amount_by_tax_id = {}
            original_amount_currency_by_tax_id = {}
            for base_line in base_lines:
                tax_details = base_line.get("tax_details", {})
                for tax_data in tax_details.get("taxes_data", []):
                    tax = tax_data.get("tax")
                    if not tax:
                        continue
                    tax_id = tax.id
                    original_amount_by_tax_id[tax_id] = original_amount_by_tax_id.get(tax_id, 0.0) + tax_data.get(
                        "tax_amount", 0.0
                    )
                    original_amount_currency_by_tax_id[tax_id] = original_amount_currency_by_tax_id.get(
                        tax_id, 0.0
                    ) + tax_data.get("tax_amount_currency", 0.0)

            for tax_group in res.get("subtotals", [{}])[0].get("tax_groups", []):
                new_amount_currency = tax_group.get("tax_amount_currency", 0.0)
                new_amount = tax_group.get("tax_amount", 0.0)
                has_override = False
                for involved_tax_id in tax_group.get("involved_tax_ids", []):
                    override = tax_context.get(involved_tax_id)
                    if not override:
                        continue
                    has_override = True
                    fixed_amount = override.get("fixed_amount", 0.0)
                    rate = override.get("rate") or 1.0
                    original_tax_amount_currency = original_amount_currency_by_tax_id.get(involved_tax_id, 0.0)
                    original_tax_amount = original_amount_by_tax_id.get(involved_tax_id, 0.0)
                    new_amount_currency += fixed_amount - original_tax_amount_currency
                    new_amount += fixed_amount / rate - original_tax_amount

                if not has_override:
                    continue

                original_amount = tax_group.get("tax_amount", 0.0)
                original_currency_amount = tax_group.get("tax_amount_currency", 0.0)
                if new_amount_currency == original_currency_amount:
                    continue

                diff = new_amount_currency - original_currency_amount
                currency_diff = new_amount - original_amount
                tax_group.update(
                    {
                        "tax_amount": new_amount,
                        "tax_amount_currency": new_amount_currency,
                    }
                )
                res["tax_amount"] += currency_diff
                res["total_amount"] += currency_diff
                res["tax_amount_currency"] += diff
                res["total_amount_currency"] += diff

        return res
