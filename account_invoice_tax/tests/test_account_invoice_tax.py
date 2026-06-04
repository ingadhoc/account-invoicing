# Part of Odoo. See LICENSE file for full copyright and licensing details.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
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
