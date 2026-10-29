from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged

from .common import LatamDocumentCommon


@tagged("post_install", "-at_install")
class TestDocumentNumber(LatamDocumentCommon):
    def test_draft_saves_without_document_number(self):
        """The form drops the native `required`, so a draft saves with no number.

        Without this module the Form refuses to save and the user is stopped while
        still filling the invoice in.
        """
        with Form(self.env["account.move"].with_context(default_move_type="in_invoice")) as bill_form:
            bill_form.partner_id = self.partner_a
            bill_form.journal_id = self.purchase_journal
            bill_form.invoice_date = self.today
            bill_form.l10n_latam_document_type_id = self.document_type
            with bill_form.invoice_line_ids.new() as line_form:
                line_form.product_id = self.product_a
                line_form.price_unit = 100.0
        bill = bill_form.save()
        self.assertTrue(bill.l10n_latam_manual_document_number)
        self.assertFalse(bill.l10n_latam_document_number)

    def test_post_without_document_number_is_refused(self):
        """What the form no longer asks for, the post does."""
        bill = self._create_invoice(self.purchase_journal, move_type="in_invoice")
        self.assertTrue(bill.l10n_latam_manual_document_number)
        with self.assertRaisesRegex(ValidationError, "Please set the document number"):
            bill.action_post()

    def test_post_with_document_number_goes_through(self):
        bill = self._create_invoice(self.purchase_journal, move_type="in_invoice")
        bill.l10n_latam_document_number = "00077-00000077"
        bill.action_post()
        self.assertEqual(bill.state, "posted")
