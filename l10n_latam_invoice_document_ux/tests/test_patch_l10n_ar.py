from odoo import tools
from odoo.exceptions import ValidationError
from odoo.tests import Form, common, tagged


@tagged("post_install", "-at_install")
class TestPatchDummy(common.TransactionCase):
    def test_dummy(self):
        # a trivial test so the test runner reports >0 tests (avoids the 0-tests warning)
        self.assertTrue(True)


# Only apply the patch while running tests
if tools.config.get("test_enable"):
    from odoo.addons.l10n_ar.tests.test_manual import TestArManual

    def test_15_liquido_producto_sales_patch(self):
        """Patcheamos para que la validacion se haga al momento de validar la factura y no antes"""

        # Verify that the default sales journals ara created as is ARCA POS
        self.assertTrue(self.journal.l10n_ar_is_pos)

        # If we create an invoice it will not use manual numbering
        invoice = self._create_invoice_ar()
        self.assertFalse(invoice.l10n_latam_manual_document_number)

        # Create a new sale journal that is not ARCA POS
        self.journal = self._create_journal("preprinted", data={"l10n_ar_is_pos": False})
        self.assertFalse(self.journal.l10n_ar_is_pos)

        doc_27_lu_a = self.env.ref("l10n_ar.dc_liq_uci_a")
        payment_term_id = self.env.ref("account.account_payment_term_end_following_month")

        # 60, 61, 27, 28, 45, 46
        # In this case manual numbering should be True and the latam document numer should be required
        with Form(self.env["account.move"].with_context(default_move_type="out_invoice")) as invoice_form:
            invoice_form.ref = "demo_liquido_producto_1: Vendor bill liquido producto (DOC 186)"
            invoice_form.partner_id = self.res_partner_adhoc
            invoice_form.invoice_payment_term_id = payment_term_id
            invoice_form.journal_id = self.journal
            invoice_form.l10n_latam_document_type_id = doc_27_lu_a
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.env.ref("product.product_product_4")
                line_form.quantity = 1
                line_form.price_unit = 100
        invoice = invoice_form.save()

        # Should fail when posting without document number
        with self.assertRaisesRegex(ValidationError, "Please set the document number"):
            invoice.action_post()

        # Adding the document number will let us to save and validate the number without any problems
        with Form(self.env["account.move"].with_context(default_move_type="out_invoice")) as invoice_form:
            invoice_form.ref = "demo_liquido_producto_1: Vendor bill liquido producto (DOC 186)"
            invoice_form.partner_id = self.res_partner_adhoc
            invoice_form.invoice_payment_term_id = payment_term_id
            invoice_form.journal_id = self.journal
            invoice_form.l10n_latam_document_type_id = doc_27_lu_a
            invoice_form.l10n_latam_document_number = "00077-00000077"
            with invoice_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.env.ref("product.product_product_4")
                line_form.quantity = 1
                line_form.price_unit = 100
        invoice = invoice_form.save()
        invoice.action_post()

    def test_16_liquido_producto_purchase_patch(self):
        """Patcheamos para que la validacion se haga al momento de validar la factura y no antes"""

        # By default purchase journals ar not ARCA POS journal
        purchase_not_pos_journal = self.env["account.journal"].search(
            [
                ("type", "=", "purchase"),
                ("company_id", "=", self.env.company.id),
                ("l10n_latam_use_documents", "=", True),
            ]
        )
        self.assertFalse(purchase_not_pos_journal.l10n_ar_is_pos)

        doc_60_lp_a = self.env.ref("l10n_ar.dc_a_cvl")
        payment_term_id = self.env.ref("account.account_payment_term_end_following_month")

        with Form(self.env["account.move"].with_context(default_move_type="in_invoice")) as bill_form:
            bill_form.ref = "demo_liquido_producto_1: Vendor bill liquido producto (DOC 186)"
            bill_form.partner_id = self.res_partner_adhoc
            bill_form.invoice_payment_term_id = payment_term_id
            bill_form.invoice_date = "2023-02-09"
            bill_form.l10n_latam_document_type_id = doc_60_lp_a
            with bill_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.env.ref("product.product_product_4")
                line_form.quantity = 1
                line_form.price_unit = 100
        bill = bill_form.save()

        self.assertEqual(bill.journal_id, purchase_not_pos_journal)

        # Should fail when posting without document number
        with self.assertRaisesRegex(ValidationError, "Please set the document number"):
            bill.action_post()

        # Create a new journal that is an ARCA POS
        purchase_pos_journal = self._create_journal("preprinted", data={"type": "purchase", "l10n_ar_is_pos": True})

        with Form(self.env["account.move"].with_context(default_move_type="in_invoice")) as bill_form:
            bill_form.ref = "demo_liquido_producto_1: Vendor bill liquido producto (DOC 186)"
            bill_form.partner_id = self.res_partner_adhoc
            bill_form.invoice_payment_term_id = payment_term_id
            bill_form.invoice_date = "2023-02-09"
            bill_form.journal_id = purchase_pos_journal
            bill_form.l10n_latam_document_type_id = doc_60_lp_a
            bill_form.l10n_latam_document_number = "00077-00000077"
            with bill_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.env.ref("product.product_product_4")
                line_form.quantity = 1
                line_form.price_unit = 100
        bill = bill_form.save()
        bill.action_post()

        # If we create an invoice it will not use manual numbering
        self.assertFalse(bill.l10n_latam_manual_document_number)

    def propagate(method1, method2):
        if method1:
            for attr in ("_returns",):
                if hasattr(method1, attr) and not hasattr(method2, attr):
                    setattr(method2, attr, getattr(method1, attr))
        return method2

    def _patch_method(cls, name, method):
        origin = getattr(cls, name)
        method.origin = origin
        wrapped = propagate(origin, method)
        wrapped.origin = origin
        setattr(cls, name, wrapped)

    _patch_method(
        TestArManual,
        "test_15_liquido_producto_sales",
        test_15_liquido_producto_sales_patch,
    )
    _patch_method(
        TestArManual,
        "test_16_liquido_producto_purchase",
        test_16_liquido_producto_purchase_patch,
    )
