from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tests.common import new_test_user
from odoo.tools import formatLang, html2plaintext


@tagged("post_install", "-at_install")
class TestInvoicePartial(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.tax = cls.company_data["default_tax_sale"]
        cls.quantities = [3.0, 7.0, 5.0]
        cls.price_unit = 100.0

    def _create_invoice(self, move_type="out_invoice"):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": self.today,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": f"line {qty}",
                            "quantity": qty,
                            "price_unit": self.price_unit,
                            "tax_ids": [Command.set(self.tax.ids)],
                        }
                    )
                    for qty in self.quantities
                ],
            }
        )

    def _apply_percentage(self, move, percentage, rounding, method, user=None):
        wizard = (
            self.env["account.invoice.partial.wizard"]
            .with_user(user or self.env.user)
            .create(
                {
                    "invoice_id": move.id,
                    "percentage_to_invoice": percentage,
                    "rounding": rounding,
                    "rounding_method": method,
                }
            )
        )
        wizard.compute_new_quantity()

    def test_percentage_applies_rounding(self):
        """The percentage scales every line quantity, rounded with the chosen precision and method.

        Totals and taxes follow the new quantities and the draft invoice keeps the same lines.
        """
        cases = [
            ("HALF-UP with 0.01 precision", 33.0, 0.01, "HALF-UP", [0.99, 2.31, 1.65]),
            ("UP with precision 1", 40.0, 1.0, "UP", [2.0, 3.0, 2.0]),
            ("DOWN with precision 1", 40.0, 1.0, "DOWN", [1.0, 2.0, 2.0]),
            ("HALF-UP with precision 1", 40.0, 1.0, "HALF-UP", [1.0, 3.0, 2.0]),
        ]
        for label, percentage, rounding, method, expected in cases:
            with self.subTest(label):
                move = self._create_invoice()
                self._apply_percentage(move, percentage, rounding, method)
                self.assertEqual(move.state, "draft")
                self.assertEqual(len(move.invoice_line_ids), len(self.quantities))
                self.assertEqual(move.invoice_line_ids.mapped("quantity"), expected)
                untaxed = sum(expected) * self.price_unit
                self.assertAlmostEqual(move.amount_untaxed, untaxed, places=2)
                self.assertAlmostEqual(move.amount_total, untaxed * (1 + self.tax.amount / 100), places=2)

    def test_wizard_as_invoicing_user_logs_total(self):
        """An invoicing user runs the wizard on invoices and credit notes and the chatter keeps the totals."""
        user = new_test_user(self.env, login="partial_invoicing_user", groups="account.group_account_invoice")
        for move_type in ("out_invoice", "out_refund"):
            with self.subTest(move_type):
                move = self._create_invoice(move_type)
                before = move.amount_total
                self._apply_percentage(move, 50.0, 0.01, "HALF-UP", user=user)
                self.assertAlmostEqual(move.amount_total, before / 2, places=2)
                log = move.message_ids.filtered(lambda m: "Invoice percentage applied" in m.body)
                self.assertEqual(len(log), 1)
                text = html2plaintext(log.body)
                self.assertIn("50.00%", text)
                self.assertIn(formatLang(self.env, before, currency_obj=move.currency_id), text)
                self.assertIn(formatLang(self.env, move.amount_total, currency_obj=move.currency_id), text)
