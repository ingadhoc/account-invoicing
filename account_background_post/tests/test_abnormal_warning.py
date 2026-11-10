##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import Command
from odoo.tests import tagged

from .common import BackgroundPostCommon


@tagged("post_install", "-at_install")
class TestAbnormalWarning(BackgroundPostCommon):
    """A vendor bill with an abnormal amount, confirmed from its form, goes through the wizard
    with the abnormal detection enabled. "Confirm now" has to post it anyway."""

    def _bill_vals(self, price_unit):
        return {
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": "2020-01-01",
            "line_ids": [Command.create({"name": "product", "price_unit": price_unit, "tax_ids": [Command.clear()]})],
        }

    def _abnormal_bill(self):
        history = self.env["account.move"].create([self._bill_vals(100) for _i in range(10)])
        history.action_post()
        bill = self.env["account.move"].create(self._bill_vals(200))
        self.assertTrue(bill.abnormal_amount_warning)
        return bill

    def _confirm_from_form(self, bill):
        """Same context the form's Confirm button sends; it reaches the wizard buttons too."""
        action = bill.with_context(disable_abnormal_invoice_detection=False).action_post()
        self.assertEqual(action.get("res_model"), "validate.account.move")
        return (
            self.env["validate.account.move"]
            .with_context(disable_abnormal_invoice_detection=False)
            .browse(action["res_id"])
        )

    def test_confirm_now_posts_the_bill(self):
        bill = self._abnormal_bill()
        wizard = self._confirm_from_form(bill)

        with self._neutralized_cursor():
            wizard.validate_move_confirm()

        self.assertEqual(bill.state, "posted")
        self.assertFalse(self.partner_a.ignore_abnormal_invoice_amount)

    def test_ignore_next_alerts_is_saved_on_the_vendor(self):
        bill = self._abnormal_bill()
        wizard = self._confirm_from_form(bill)
        wizard.ignore_abnormal_amount = True

        with self._neutralized_cursor():
            wizard.validate_move_confirm()

        self.assertEqual(bill.state, "posted")
        self.assertTrue(self.partner_a.ignore_abnormal_invoice_amount)
        self.assertFalse(self.env["account.move"].create(self._bill_vals(300)).abnormal_amount_warning)
