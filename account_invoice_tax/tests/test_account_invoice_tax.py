from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountInvoiceTax(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_tax = cls.env["account.tax"].create(
            {
                "name": "VAT Purchase 21",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "purchase",
                "company_id": cls.env.company.id,
            }
        )
        cls.sale_tax = cls.env["account.tax"].create(
            {
                "name": "VAT Sale 21",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "sale",
                "company_id": cls.env.company.id,
            }
        )
        cls.fixed_tax = cls.env["account.tax"].create(
            {
                "name": "Fixed Tax 1",
                "amount_type": "fixed",
                "amount": 1.0,
                "type_tax_use": "purchase",
                "company_id": cls.env.company.id,
            }
        )

    def _build_move(self, move_type, taxes):
        return self._create_invoice_one_line(
            move_type=move_type,
            price_unit=1000.0,
            tax_ids=taxes,
        )

    def _open_wizard(self, move):
        return (
            self.env["account.invoice.tax"]
            .with_context(
                active_model="account.move",
                active_ids=move.ids,
            )
            .create({})
        )

    def _tax_line(self, move, tax):
        return move.line_ids.filtered(lambda l: l.tax_line_id == tax)

    def _set_amount_and_apply(self, move, amount, tax=None):
        wizard = self._open_wizard(move)
        wizard.tax_line_ids.amount = amount
        wizard.action_update_tax()
        return self._tax_line(move, tax or self.purchase_tax)

    def test_in_invoice_positive_amount(self):
        move = self._build_move("in_invoice", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, 100.0)
        self.assertEqual(tax_line.debit, 100.0)
        self.assertEqual(tax_line.credit, 0.0)
        self.assertEqual(tax_line.balance, 100.0)
        self.assertEqual(tax_line.amount_currency, 100.0)

    def test_in_invoice_negative_amount_keeps_negative(self):
        """Ticket #116742: cargar -100 en wizard sobre in_invoice debe
        preservar el signo negativo en balance y amount_currency."""
        move = self._build_move("in_invoice", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, -100.0)
        self.assertEqual(tax_line.debit, 0.0)
        self.assertEqual(tax_line.credit, 100.0)
        self.assertEqual(tax_line.balance, -100.0)
        self.assertEqual(tax_line.amount_currency, -100.0)

    def test_in_refund_positive_amount(self):
        move = self._build_move("in_refund", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, 100.0)
        self.assertEqual(tax_line.debit, 0.0)
        self.assertEqual(tax_line.credit, 100.0)
        self.assertEqual(tax_line.balance, -100.0)
        self.assertEqual(tax_line.amount_currency, -100.0)

    def test_in_refund_negative_amount_keeps_positive(self):
        move = self._build_move("in_refund", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, -100.0)
        self.assertEqual(tax_line.debit, 100.0)
        self.assertEqual(tax_line.credit, 0.0)
        self.assertEqual(tax_line.balance, 100.0)
        self.assertEqual(tax_line.amount_currency, 100.0)

    def test_wizard_raises_on_out_invoice(self):
        move = self._build_move("out_invoice", self.sale_tax)
        with self.assertRaises(UserError):
            self._open_wizard(move)

    def test_wizard_raises_on_out_refund(self):
        move = self._build_move("out_refund", self.sale_tax)
        with self.assertRaises(UserError):
            self._open_wizard(move)

    def test_wizard_amount_is_applied_to_accounting_entry(self):
        """El monto ingresado en el wizard se refleja en el apunte contable
        y se persiste en tax_override_data para impuestos fijos."""
        move = self._build_move("in_invoice", self.fixed_tax)
        tax_line = self._set_amount_and_apply(move, 750.0, tax=self.fixed_tax)

        self.assertAlmostEqual(abs(tax_line.balance), 750.0)
        self.assertAlmostEqual(move.tax_override_data[str(self.fixed_tax.id)]["amount"], 750.0)

    def test_override_survives_price_change_and_new_line(self):
        """El override del impuesto fijo sobrevive tanto a un cambio de precio
        como al agregado de una nueva línea en la factura."""
        move = self._build_move("in_invoice", self.fixed_tax)
        self._set_amount_and_apply(move, 320.0, tax=self.fixed_tax)

        # Cambio de precio → dispara recomputación de líneas de impuesto
        move.invoice_line_ids[0].write({"price_unit": 2000.0})
        self.assertAlmostEqual(
            abs(self._tax_line(move, self.fixed_tax).balance),
            320.0,
            msg="Override lost after price change",
        )

        # Agregar línea nueva → segunda recomputación
        move.write(
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Extra line",
                            "quantity": 1.0,
                            "price_unit": 500.0,
                            "account_id": self.company_data["default_account_expense"].id,
                            "tax_ids": [Command.set(self.fixed_tax.ids)],
                        }
                    )
                ]
            }
        )
        self.assertAlmostEqual(
            abs(self._tax_line(move, self.fixed_tax).balance),
            320.0,
            msg="Override lost after adding a new line",
        )

    def test_percent_tax_applied_to_entry_but_not_persisted(self):
        """El override de un impuesto porcentual se aplica al apunte contable
        pero no se persiste en tax_override_data (siempre se recomputa)."""
        # Se usa 150 en lugar del valor natural (21% de 1000 = 210) para
        # distinguir el override del cómputo automático.
        move = self._build_move("in_invoice", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, 150.0)

        self.assertAlmostEqual(abs(tax_line.balance), 150.0)
        self.assertNotIn(str(self.purchase_tax.id), move.tax_override_data or {})
