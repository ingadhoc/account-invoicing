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
        """Restore manually-set tax amounts after the core recomputes tax lines.

        Also fixes a core Odoo ordering issue: within ``_sync_dynamic_lines``
        the ``ExitStack`` unwinds in LIFO order, so ``line._sync_invoice``
        exits *before* ``_sync_tax_lines``.  When the invoice date changes on
        a foreign-currency invoice, ``line._sync_invoice`` rewrites the
        ``balance`` of every line (including tax lines) for the new exchange
        rate.  ``_sync_tax_lines`` then sees those touched balances and
        concludes that the tax amounts were manually edited
        (``round_from_tax_lines = True``), so it preserves the old totals
        even though a base line was deleted at the same time.

        We detect that scenario here and force a full recompute from base
        lines so that the amounts correctly reflect only the remaining lines.
        """
        # Capture state before the main yield so we can detect the scenario.
        records = container.get("records", self)
        _before_state = {
            move: {
                "rate": move.invoice_currency_rate,
                "taxed_base_ids": frozenset(
                    move.line_ids.filtered(lambda l: l.display_type == "product" and l.tax_ids).ids
                ),
            }
            for move in records
            if move.id and move.state == "draft"
        }

        with super()._sync_tax_lines(container):
            yield

        AccountTax = self.env["account.tax"]
        for move in container.get("records", self):
            # Fix: when the invoice currency rate changed at the same time as a
            # taxed base line was deleted, the core may have preserved the stale
            # tax totals.  Re-run the computation from base lines in that case.
            if move.state == "draft" and move.id:
                before = _before_state.get(move)
                if before and before["rate"] != move.invoice_currency_rate:
                    current_taxed_base_ids = frozenset(
                        move.line_ids.filtered(lambda l: l.display_type == "product" and l.tax_ids).ids
                    )
                    if before["taxed_base_ids"] - current_taxed_base_ids:
                        # Force a fresh recompute from base lines.
                        base_lines_values, tax_lines_values = move._get_rounded_base_and_tax_lines(
                            round_from_tax_lines=False
                        )
                        AccountTax._add_accounting_data_in_base_lines_tax_details(
                            base_lines_values,
                            move.company_id,
                            include_caba_tags=move.always_tax_exigible,
                        )
                        tax_results = AccountTax._prepare_tax_lines(
                            base_lines_values,
                            move.company_id,
                            tax_lines=tax_lines_values,
                        )
                        for _tax_line_vals, _grouping_key, to_update in tax_results["tax_lines_to_update"]:
                            _tax_line_vals["record"].write(dict(to_update))
                        if tax_results.get("tax_lines_to_delete"):
                            self.env["account.move.line"].browse(
                                v["record"].id for v in tax_results["tax_lines_to_delete"]
                            ).with_context(dynamic_unlink=True).unlink()
                        if tax_results.get("tax_lines_to_add"):
                            self.env["account.move.line"].create(
                                [
                                    {**vals, "display_type": "tax", "move_id": move.id}
                                    for vals in tax_results["tax_lines_to_add"]
                                ]
                            )
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
        if not overrides or self.state == "posted":
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

            sign = 1 if debit or debit_cc else -1
            # When in_invoice/in_receipt and amount < 0, the value is placed in
            # credit (debit=0), making sign=-1. That double-negates amount_cc and
            # produces a positive balance (debit side) instead of credit. Force
            # sign=1 so the negative amount stays on the credit side.
            if self.move_type in ("in_invoice", "in_receipt") and amount < 0:
                sign = 1
            line_vals = {
                "debit": debit_cc if not_company_currency else debit,
                "credit": credit_cc if not_company_currency else credit,
                "balance": (amount_cc if not_company_currency else amount) * sign,
            }
            if not_company_currency and amount:
                line_vals["amount_currency"] = amount * sign
            line.write(line_vals)
