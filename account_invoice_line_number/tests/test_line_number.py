import ast

from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountInvoiceLineNumber(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.tax = cls.company_data["default_tax_sale"]
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_date": cls.today,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": name,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "sequence": sequence,
                            "tax_ids": [Command.set(cls.tax.ids)],
                        }
                    )
                    for name, sequence in (("A", 10), ("B", 20), ("C", 30))
                ],
            }
        )

    def _numbers(self):
        # computed fields have no depends: drop the cache as a form reload would
        self.invoice.invalidate_recordset(["number_lines"])
        self.invoice.line_ids.invalidate_recordset(["number"])
        return {line.name: line.number for line in self.invoice.invoice_line_ids}

    def test_line_number(self):
        """Invoice lines are numbered 1..N following their sequence.

        Covers: numbering by position, renumbering when the sequence changes,
        and that only product lines are numbered (not tax/payment term lines).
        """
        lines = {line.name: line for line in self.invoice.invoice_line_ids}
        with self.subTest("each product line gets its position following the sequence"):
            self.assertEqual(self._numbers(), {"A": 1, "B": 2, "C": 3})

        with self.subTest("reversing the sequences renumbers the lines"):
            lines["A"].sequence = 30
            lines["C"].sequence = 10
            self.assertEqual(self._numbers(), {"A": 3, "B": 2, "C": 1})

        with self.subTest("tax and payment term lines are not numbered"):
            other_lines = self.invoice.line_ids - self.invoice.invoice_line_ids
            self.assertTrue(other_lines)
            self.assertFalse(any(other_lines.mapped("number")))
            self.assertEqual(
                set(ast.literal_eval(self.invoice.number_lines)),
                set(self.invoice.invoice_line_ids.ids),
            )
