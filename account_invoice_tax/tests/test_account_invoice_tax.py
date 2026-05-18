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

    def _set_amount_and_apply(self, move, amount):
        wizard = self._open_wizard(move)
        wizard.tax_line_ids.amount = amount
        wizard.action_update_tax()
        return self._tax_line(move, self.purchase_tax)

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
