from contextlib import contextmanager

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # Stores manually-overridden tax amounts keyed by tax id (as string).
    # Structure: { "<tax_id>": {"amount": float, "rate": float} }
    # Only fixed-amount taxes are stored here; percentage taxes are always
    # recomputed automatically.
    tax_override_data = fields.Json()

    def sync_tax_override_from_tax_totals(self):
        """Rebuild ``tax_override_data`` from the current ``tax_totals`` widget value.

        Iterates every tax group in ``tax_totals`` and, for each fixed-amount
        tax found, stores the displayed amounts as an override so they survive
        future recomputations.

        ``tax_totals`` structure (relevant fields)::

            {
                "subtotals": [{
                    "tax_groups": [{
                        "involved_tax_ids": [<tax_id>, ...],
                        "tax_amount":          <float>,   # company currency
                    }, ...]
                }, ...]
            }

        ``amount`` (invoice-currency) → ``tax_amount_currency`` when the
        invoice is in a foreign currency, otherwise ``tax_amount``.
        ``amount_company_currency`` → ``tax_amount`` (always company currency),
        or 0.0 when the invoice is in company currency (field unused in that
        case, see ``_apply_tax_overrides``).
        """
        for rec in self.filtered(lambda m: m.move_type in ("in_invoice", "in_refund", "in_receipt")):
            tax_totals = rec.tax_totals
            if not tax_totals:
                continue

            is_company_currency = rec.currency_id == rec.company_currency_id
            new_overrides = {}

            for subtotal in tax_totals.get("subtotals", []):
                for tax_group in subtotal.get("tax_groups", []):
                    tax_amount = tax_group.get("tax_amount", 0.0)
                    tax_amount_currency = tax_group.get("tax_amount_currency", 0.0)

                    for tax_id in tax_group.get("involved_tax_ids", []):
                        tax = rec.env["account.tax"].browse(tax_id)
                        if not tax.exists() or tax.amount_type != "fixed":
                            continue

                        if is_company_currency:
                            amount = tax_amount
                            rate = 1
                        else:
                            amount = tax_amount_currency
                            rate = rec.invoice_currency_rate or 1.0

                        new_overrides[str(tax_id)] = {
                            "amount": amount,
                            "rate": rate,
                        }

            rec.tax_override_data = new_overrides or False

    # ------------------------------------------------------------------
    # Tax-totals widget: inject override amounts so the widget reflects
    # the manually-set values instead of the recomputed ones.
    # ------------------------------------------------------------------

    def _compute_tax_totals(self):
        for move in self:
            overrides = move.tax_override_data or {}
            if not overrides:
                super(AccountMove, move)._compute_tax_totals()
                continue

            tax_context = {
                "tax_context": {
                    int(tax_id): {
                        "fixed_amount": (vals["amount"]),
                        "rate": (move.invoice_currency_rate or 1.0),
                    }
                    for tax_id, vals in overrides.items()
                },
            }
            super(AccountMove, move.with_context(**tax_context))._compute_tax_totals()

    # ------------------------------------------------------------------
    # Re-apply overrides after every tax-line recomputation so that the
    # amounts set through the wizard survive any subsequent edits on the
    # invoice lines.
    # ------------------------------------------------------------------

    @contextmanager
    def _sync_tax_lines(self, container):
        """Restore manually-set tax amounts after the core recomputes tax lines."""
        with super()._sync_tax_lines(container):
            yield
        for move in container.get("records", self):
            move._apply_tax_overrides()

    def _apply_tax_overrides(self, other_taxes_override=False):
        """Re-write values from ``tax_override_data`` onto the matching tax lines.

        Only overrides for fixed-amount taxes are applied; percentage-based
        taxes are always recomputed unless they are present in the
        ``other_taxes_override`` dictionary.
        """
        overrides = self.tax_override_data or {}
        if other_taxes_override:
            # Percentage-based tax overrides are not stored in ``tax_override_data``
            # as they don't need to survive recomputations, but we still want to
            # apply them on the current tax lines.
            overrides.update(other_taxes_override)
        if not overrides:
            return

        move_currency = self.currency_id
        company_currency = self.company_currency_id
        not_company_currency = move_currency and move_currency != company_currency
        for line in self.line_ids.filtered(lambda l: l.tax_line_id and str(l.tax_line_id.id) in overrides):
            vals = overrides[str(line.tax_line_id.id)]
            rate = line.move_id.invoice_currency_rate or 1.0
            amount = vals.get("amount", 0.0)
            amount_cc = amount / rate
            debit = credit = debit_cc = credit_cc = 0.0
            if self.move_type in ("in_invoice", "in_receipt"):
                if amount > 0:
                    debit, debit_cc = amount, amount_cc
                elif amount < 0:
                    credit, credit_cc = -amount, -amount_cc
            else:
                if amount > 0:
                    credit, credit_cc = amount, amount_cc
                elif amount < 0:
                    debit, debit_cc = -amount, -amount_cc

            line_vals = {
                "debit": debit_cc if not_company_currency else debit,
                "credit": credit_cc if not_company_currency else credit,
                "balance": ((amount_cc if not_company_currency else amount) * (1 if debit or debit_cc else -1)),
            }
            if not_company_currency and amount:
                line_vals["amount_currency"] = amount * (1 if debit or debit_cc else -1)
            line.write(line_vals)
