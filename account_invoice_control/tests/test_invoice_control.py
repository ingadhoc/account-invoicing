from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestInvoiceControl(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group = cls.env.ref("account_invoice_control.group_restrict_edit_invoice")
        invoicing = cls.env.ref("account.group_account_invoice")
        cls.restricted_user = cls.env["res.users"].create(
            {
                "name": "Restricted",
                "login": "restricted_aic",
                "group_ids": [(6, 0, (invoicing | group).ids)],
            }
        )
        cls.free_user = cls.env["res.users"].create(
            {
                "name": "Free",
                "login": "free_aic",
                "group_ids": [(6, 0, invoicing.ids)],
            }
        )
        order = (
            cls.env["sale.order"]
            .sudo()
            .create(
                {
                    "partner_id": cls.partner_a.id,
                    "order_line": [(0, 0, {"product_id": cls.product_a.id, "product_uom_qty": 1})],
                }
            )
        )
        # link the sale line by hand: invoicing the order goes through modules that vary per build
        cls.invoice_from_order = cls.init_invoice("out_invoice", products=cls.product_a, post=False)
        cls.invoice_from_order.invoice_line_ids.sudo().sale_line_ids = [(6, 0, order.order_line.ids)]
        cls.invoice_without_order = cls.init_invoice("out_invoice", products=cls.product_a, post=False)
        cls.vendor_bill = cls.init_invoice("in_invoice", products=cls.product_a, post=False)

    def _assert_editable(self, move, user, editable):
        """Try to change the fields the module protects, as ``user``."""
        move = move.with_user(user)
        # Form keeps one set of modifiers per field name, so fields repeated in
        # the view per move type (invoice_date, fiscal_position_id) are skipped
        for fname, value in (
            ("partner_id", self.partner_b),
            ("invoice_payment_term_id", self.pay_terms_a),
        ):
            with Form(move) as form:
                if editable:
                    setattr(form, fname, value)
                else:
                    with self.assertRaises(AssertionError, msg=fname):
                        setattr(form, fname, value)

    def test_restriction_by_group_and_origin(self):
        cases = (
            # label, move, user, has_sales, restricted, can edit
            (
                "restricted user can not edit an invoice that comes from a sale order",
                self.invoice_from_order,
                self.restricted_user,
                True,
                True,
                False,
            ),
            (
                "restricted user edits an invoice without sale order",
                self.invoice_without_order,
                self.restricted_user,
                False,
                True,
                True,
            ),
            (
                "a user outside the group edits an invoice from a sale order",
                self.invoice_from_order,
                self.free_user,
                True,
                False,
                True,
            ),
            ("restricted user edits a vendor bill", self.vendor_bill, self.restricted_user, False, True, True),
        )
        for label, move, user, has_sales, restricted, editable in cases:
            with self.subTest(label):
                as_user = move.with_user(user)
                self.assertEqual(as_user.has_sales, has_sales)
                self.assertEqual(as_user.restrict_edit_invoice, restricted)
                self._assert_editable(move, user, editable)
