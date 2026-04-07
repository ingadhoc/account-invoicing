from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountInvoiceTaxWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.tax_group = cls.env["account.tax.group"].create(
            {
                "name": "Test Tax Group Fixed",
                "sequence": 99,
            }
        )
        cls.tax_fixed_1 = cls.env["account.tax"].create(
            {
                "name": "Fixed Tax A",
                "amount_type": "fixed",
                "amount": 10.0,
                "type_tax_use": "purchase",
                "tax_group_id": cls.tax_group.id,
            }
        )
        cls.tax_fixed_2 = cls.env["account.tax"].create(
            {
                "name": "Fixed Tax B",
                "amount_type": "fixed",
                "amount": 20.0,
                "type_tax_use": "purchase",
                "tax_group_id": cls.tax_group.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Vendor Fixed"})

    def _make_wizard(self, move):
        ctx = {"active_ids": [move.id], "active_model": "account.move"}
        defaults = self.env["account.invoice.tax"].with_context(**ctx).default_get(["move_id", "tax_line_ids"])
        return self.env["account.invoice.tax"].with_context(**ctx).create(defaults)

    def _get_group_totals(self, move):
        """Return (tax_amount_cc, tax_amount_currency) for the shared tax group."""
        tax_totals = move.tax_totals or {}
        for subtotal in tax_totals.get("subtotals", []):
            for tg in subtotal.get("tax_groups", []):
                if tg.get("id") == self.tax_group.id:
                    return tg.get("tax_amount", 0.0), tg.get("tax_amount_currency", 0.0)
        return 0.0, 0.0

    def test_fixed_taxes_same_group_company_currency(self):
        """Wizard changes to two fixed taxes in same group update overrides and tax_totals."""
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_fixed_1.id, self.tax_fixed_2.id])],
                        },
                    )
                ],
            }
        )

        wizard = self._make_wizard(move)

        for line in wizard.tax_line_ids:
            if line.tax_id == self.tax_fixed_1:
                line.amount = 15.0
            elif line.tax_id == self.tax_fixed_2:
                line.amount = 25.0

        wizard.action_update_tax()

        # Both taxes persisted in tax_override_data with new amounts
        overrides = move.tax_override_data or {}
        self.assertAlmostEqual(overrides[str(self.tax_fixed_1.id)]["amount"], 15.0, places=2)
        self.assertAlmostEqual(overrides[str(self.tax_fixed_2.id)]["amount"], 25.0, places=2)

        # Actual tax lines on the move reflect new values (in_invoice → debit)
        line_1 = move.line_ids.filtered(lambda l: l.tax_line_id == self.tax_fixed_1)
        line_2 = move.line_ids.filtered(lambda l: l.tax_line_id == self.tax_fixed_2)
        self.assertAlmostEqual(line_1.debit, 15.0, places=2)
        self.assertAlmostEqual(line_2.debit, 25.0, places=2)

        # tax_totals group total = 15 + 25 = 40 in company currency
        group_amt_cc, _group_amt_currency = self._get_group_totals(move)
        self.assertAlmostEqual(group_amt_cc, 40.0, places=2)

    def test_fixed_taxes_same_group_foreign_currency(self):
        """Wizard changes in a foreign-currency invoice persist and tax_totals group is correct."""
        usd = self.env["res.currency"].with_context(active_test=False).search([("name", "=", "USD")], limit=1)
        if not usd:
            usd = self.env["res.currency"].create({"name": "USD", "symbol": "USD$"})
        usd.active = True

        # Ensure a fresh rate today: 1 company_currency = 0.5 USD  →  1 USD = 2 company_currency
        self.env["res.currency.rate"].search(
            [
                ("currency_id", "=", usd.id),
                ("name", "=", fields.Date.today()),
                ("company_id", "=", self.env.company.id),
            ]
        ).unlink()
        self.env["res.currency.rate"].create(
            {
                "currency_id": usd.id,
                "rate": 0.5,
                "name": fields.Date.today(),
                "company_id": self.env.company.id,
            }
        )

        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "currency_id": usd.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Service",
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, [self.tax_fixed_1.id, self.tax_fixed_2.id])],
                        },
                    )
                ],
            }
        )

        # Read rate from the move so assertions don't hardcode the conversion direction
        rate = move.invoice_currency_rate

        wizard = self._make_wizard(move)

        for line in wizard.tax_line_ids:
            if line.tax_id == self.tax_fixed_1:
                line.amount = 15.0  # USD
            elif line.tax_id == self.tax_fixed_2:
                line.amount = 25.0  # USD

        wizard.action_update_tax()

        # Overrides stored in invoice currency (USD)
        overrides = move.tax_override_data or {}
        self.assertAlmostEqual(overrides[str(self.tax_fixed_1.id)]["amount"], 15.0, places=2)
        self.assertAlmostEqual(overrides[str(self.tax_fixed_2.id)]["amount"], 25.0, places=2)

        # Tax lines: amount_currency in USD, debit in company currency
        line_1 = move.line_ids.filtered(lambda l: l.tax_line_id == self.tax_fixed_1)
        line_2 = move.line_ids.filtered(lambda l: l.tax_line_id == self.tax_fixed_2)
        self.assertAlmostEqual(abs(line_1.amount_currency), 15.0, places=2)
        self.assertAlmostEqual(abs(line_2.amount_currency), 25.0, places=2)
        self.assertAlmostEqual(line_1.debit, 15.0 / rate, places=2)
        self.assertAlmostEqual(line_2.debit, 25.0 / rate, places=2)

        # tax_totals group: invoice-currency total = 40 USD, company-currency = 40 / rate
        group_amt_cc, group_amt_currency = self._get_group_totals(move)
        self.assertAlmostEqual(group_amt_currency, 40.0, places=2)
        self.assertAlmostEqual(group_amt_cc, 40.0 / rate, places=2)
