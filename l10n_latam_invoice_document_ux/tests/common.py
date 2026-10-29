from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class LatamDocumentCommon(AccountTestInvoicingCommon):
    """Base for the module's tests: a document type and journals that use documents,
    built on l10n_latam_invoice_document alone, so no localization has to be installed.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        country = cls.env.company.account_fiscal_country_id
        if not country:
            raise ValueError("the test company has no fiscal country: no document type can be created")
        cls.document_type = cls.env["l10n_latam.document.type"].create(
            {
                "name": "Test Invoice",
                "code": "001",
                "doc_code_prefix": "TI",
                "internal_type": "invoice",
                "country_id": country.id,
            }
        )
        cls.journal = cls._create_journal("sale", use_documents=True)
        cls.other_journal = cls._create_journal("sale", use_documents=True)
        cls.plain_journal = cls._create_journal("sale", use_documents=False)
        # numbering is manual on purchase journals, which is where the deferred
        # requirement of the document number shows
        cls.purchase_journal = cls._create_journal("purchase", use_documents=True)

    @classmethod
    def _create_journal(cls, journal_type, use_documents):
        default_journal = cls.company_data["default_journal_%s" % journal_type]
        code = cls._next_journal_code()
        return cls.env["account.journal"].create(
            {
                "name": "Test %s %s" % (journal_type, code),
                "code": code,
                "type": journal_type,
                "l10n_latam_use_documents": use_documents,
                "default_account_id": default_journal.default_account_id.id,
            }
        )

    @classmethod
    def _next_journal_code(cls):
        """A code no journal of this company holds yet, so the tests never collide
        with whatever the chart template brought."""
        taken = set(cls.env["account.journal"].search([("company_id", "=", cls.env.company.id)]).mapped("code"))
        for number in range(1, 1000):
            code = "T%03d" % number
            if code not in taken:
                return code
        raise ValueError("no free journal code left for the test")

    def _create_invoice(self, journal, move_type="out_invoice", post=False, **values):
        invoice = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "journal_id": journal.id,
                "invoice_date": self.today,
                "l10n_latam_document_type_id": self.document_type.id,
                "invoice_line_ids": [Command.create({"product_id": self.product_a.id, "price_unit": 100.0})],
                **values,
            }
        )
        if post:
            invoice.action_post()
        return invoice
