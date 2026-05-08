# Part of Odoo. See LICENSE file for full copyright and licensing details.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountInvoiceTax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Supplier Test", "supplier_rank": 1})
        cls._acct_expense = cls.env["account.account"].create(
            {"name": "Test Expense", "code": "TST.EXP.INV", "account_type": "expense"}
        )
        acct_tax = cls.env["account.account"].create(
            {"name": "Test Tax", "code": "TST.TAX.INV", "account_type": "liability_current"}
        )
        cls.tax_fixed = cls._make_tax(cls, "Fixed Tax Test", "fixed", 1.0, acct_tax)
        cls.tax_percent = cls._make_tax(cls, "Percent Tax 21%", "percent", 21.0, acct_tax)

    def _make_tax(self, name, amount_type, amount, account):
        tax = self.env["account.tax"].create(
            {"name": name, "amount_type": amount_type, "amount": amount, "type_tax_use": "purchase"}
        )
        for repartition in tax.invoice_repartition_line_ids + tax.refund_repartition_line_ids:
            if repartition.repartition_type == "tax":
                repartition.account_id = account
        return tax

    def _make_invoice(self, tax):
        return self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Line",
                            "quantity": 1.0,
                            "price_unit": 1000.0,
                            "account_id": self._acct_expense.id,
                            "tax_ids": [Command.set(tax.ids)],
                        }
                    )
                ],
            }
        )

    def _make_wizard(self, invoice, lines_vals):
        return (
            self.env["account.invoice.tax"]
            .with_context(
                active_model="account.move",
                active_ids=invoice.ids,
            )
            .create(
                {
                    "move_id": invoice.id,
                    "tax_line_ids": [Command.create(v) for v in lines_vals],
                }
            )
        )

    def _tax_line(self, invoice, tax):
        return invoice.line_ids.filtered(lambda l: l.tax_line_id == tax)

    def test_wizard_amount_is_applied_to_accounting_entry(self):
        """El monto ingresado en el wizard se refleja en el apunte contable
        y se persiste en tax_override_data para impuestos fijos."""
        invoice = self._make_invoice(self.tax_fixed)
        self._make_wizard(
            invoice, [{"tax_id": self.tax_fixed.id, "amount": 750.0, "new_tax": False}]
        ).action_update_tax()

        self.assertAlmostEqual(abs(self._tax_line(invoice, self.tax_fixed).balance), 750.0)
        self.assertAlmostEqual(invoice.tax_override_data[str(self.tax_fixed.id)]["amount"], 750.0)

    def test_override_survives_price_change_and_new_line(self):
        """El override del impuesto fijo sobrevive tanto a un cambio de precio
        como al agregado de una nueva línea en la factura."""
        invoice = self._make_invoice(self.tax_fixed)
        self._make_wizard(
            invoice, [{"tax_id": self.tax_fixed.id, "amount": 320.0, "new_tax": False}]
        ).action_update_tax()

        # Cambio de precio → dispara recomputación de líneas de impuesto
        invoice.invoice_line_ids[0].write({"price_unit": 2000.0})
        self.assertAlmostEqual(
            abs(self._tax_line(invoice, self.tax_fixed).balance),
            320.0,
            msg="Override lost after price change",
        )

        # Agregar línea nueva → segunda recomputación
        invoice.write(
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Extra line",
                            "quantity": 1.0,
                            "price_unit": 500.0,
                            "account_id": self._acct_expense.id,
                            "tax_ids": [Command.set(self.tax_fixed.ids)],
                        }
                    )
                ]
            }
        )
        self.assertAlmostEqual(
            abs(self._tax_line(invoice, self.tax_fixed).balance),
            320.0,
            msg="Override lost after adding a new line",
        )

    def test_percent_tax_applied_to_entry_but_not_persisted(self):
        """El override de un impuesto porcentual se aplica al apunte contable
        pero no se persiste en tax_override_data (siempre se recomputa)."""
        invoice = self._make_invoice(self.tax_percent)
        # Se usa 150 en lugar del valor natural (21% de 1000 = 210) para
        # distinguir el override del cómputo automático.
        self._make_wizard(
            invoice, [{"tax_id": self.tax_percent.id, "amount": 150.0, "new_tax": False}]
        ).action_update_tax()

        self.assertAlmostEqual(abs(self._tax_line(invoice, self.tax_percent).balance), 150.0)
        self.assertNotIn(str(self.tax_percent.id), invoice.tax_override_data or {})


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
