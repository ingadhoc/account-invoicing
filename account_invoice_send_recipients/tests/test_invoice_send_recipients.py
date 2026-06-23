from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestInvoiceSendRecipients(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Customer Company",
                "is_company": True,
                "email": "company@example.com",
            }
        )
        cls.accountant = cls.env["res.partner"].create(
            {
                "name": "Accountant",
                "parent_id": cls.customer.id,
                "type": "contact",
                "email": "accountant@example.com",
                "send_invoice_by_email": True,
            }
        )
        cls.admin_office = cls.env["res.partner"].create(
            {
                "name": "Admin Office",
                "parent_id": cls.accountant.id,
                "type": "invoice",
                "email": "admin@example.com",
                "send_invoice_by_email": True,
            }
        )
        cls.no_email = cls.env["res.partner"].create(
            {
                "name": "No Email",
                "parent_id": cls.customer.id,
                "email": False,
                "send_invoice_by_email": True,
            }
        )
        cls.not_flagged = cls.env["res.partner"].create(
            {
                "name": "Not Flagged",
                "parent_id": cls.customer.id,
                "email": "other@example.com",
                "send_invoice_by_email": False,
            }
        )

    def _create_invoice(self, move_type, post=True):
        return self.init_invoice(
            move_type,
            partner=self.customer,
            products=self.product_a,
            post=post,
        )

    def test_extra_recipients_out_invoice(self):
        invoice = self._create_invoice("out_invoice")
        recipients = invoice._get_invoice_extra_recipients()
        self.assertEqual(recipients, self.accountant | self.admin_office)
        self.assertNotIn(self.no_email, recipients)
        self.assertNotIn(self.not_flagged, recipients)

    def test_extra_recipients_out_refund(self):
        refund = self._create_invoice("out_refund")
        self.assertEqual(
            refund._get_invoice_extra_recipients(),
            self.accountant | self.admin_office,
        )

    def test_extra_recipients_vendor_bill_empty(self):
        bill = self.init_invoice(
            "in_invoice",
            partner=self.customer,
            products=self.product_a,
            post=True,
        )
        self.assertFalse(bill._get_invoice_extra_recipients())

    def test_wizard_includes_extra_recipients_without_duplicates(self):
        self.customer.send_invoice_by_email = True
        invoice = self._create_invoice("out_invoice")
        wizard = (
            self.env["account.move.send.wizard"]
            .with_context(
                active_model="account.move",
                active_ids=invoice.ids,
            )
            .create({"move_id": invoice.id})
        )

        partners = wizard.mail_partner_ids
        self.assertIn(self.customer, partners)
        self.assertIn(self.accountant, partners)
        self.assertIn(self.admin_office, partners)
        self.assertNotIn(self.no_email, partners)
        self.assertNotIn(self.not_flagged, partners)
        self.assertEqual(len(partners), len(set(partners.ids)))
