from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LatamDocumentCommon


@tagged("post_install", "-at_install")
class TestJournalChange(LatamDocumentCommon):
    def test_journal_change_on_posted_move(self):
        """A posted move cannot be moved to a journal that uses documents.

        Odoo lets the journal change through when the number is cleared; this module
        does not.
        """
        invoice = self._create_invoice(self.journal, post=True)
        self.assertTrue(invoice.l10n_latam_use_documents)
        with self.assertRaisesRegex(UserError, "You cannot change the journal of a posted move"):
            invoice.write({"name": "/", "journal_id": self.other_journal.id})

    def test_journal_change_on_posted_move_to_plain_journal(self):
        """The constraint looks at the journal it moves to, so a journal without
        documents is still allowed. Pinned as it stands: widening it would change
        what the module does."""
        invoice = self._create_invoice(self.journal, post=True)
        invoice.write({"name": "/", "journal_id": self.plain_journal.id})
        self.assertEqual(invoice.journal_id, self.plain_journal)

    def test_journal_change_on_draft_move(self):
        """A draft move can still change its journal."""
        invoice = self._create_invoice(self.journal)
        invoice.journal_id = self.other_journal
        self.assertEqual(invoice.journal_id, self.other_journal)
