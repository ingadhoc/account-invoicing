import base64
from unittest.mock import patch

from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

# 1x1 PNG, different from Odoo's placeholder logo
PNG = base64.b64encode(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360f8cfc0f01f0005000201a5f645400000000049454e44ae426082"
    )
).decode()
REPORT = "account_thermal_ticket.report_thermal_invoice_html"


@tagged("post_install", "-at_install")
class TestThermalTicket(AccountTestInvoicingCommon):
    # Assertions never print the rendered ticket or an image: a failing
    # assertIn/assertEqual would dump it, binary included, into the test log.
    def _text(self, content):
        if isinstance(content, bytes):
            content = content.decode(errors="replace")
        return content.replace("\x00", "")

    def assertTicketHas(self, needle, html, present=True):
        found = needle in html
        if found != present:
            state = "missing from" if present else "unexpectedly in"
            self.fail(f"{needle!r} {state} the rendered ticket ({len(html)} chars)")

    def assertSameImage(self, value, expected):
        if value != expected:
            self.fail("the header logo is not the expected image")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "VAT 21",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "sale",
                "company_id": cls.env.company.id,
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_a.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Thermal product",
                            "quantity": 2.0,
                            "price_unit": 100.0,
                            "discount": 10.0,
                            "tax_ids": [Command.set(cls.tax.ids)],
                        }
                    )
                ],
            }
        )
        cls.line = cls.invoice.invoice_line_ids

    def test_report_name_default(self):
        self.assertEqual(self.invoice._get_thermal_receipt_report_name(), REPORT)

    def test_print_action(self):
        action = self.invoice.action_print_thermal_receipt()
        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "thermal_print")
        self.assertEqual(action["context"]["report_name"], REPORT)
        self.assertEqual(action["context"]["invoice_id"], self.invoice.id)

    def test_report_has_no_binding(self):
        report = self.env.ref("account_thermal_ticket.action_report_thermal_invoice_html")
        self.assertFalse(report.binding_model_id)

    def test_line_prices_net(self):
        prices = self.line._thermal_line_prices()
        self.assertEqual(prices["price_unit"], 100.0)
        self.assertEqual(prices["amount"], self.line.price_subtotal)
        self.assertEqual(prices["discount"], 10.0)

    def test_line_prices_tax_included(self):
        with patch.object(type(self.invoice), "_thermal_prices_include_taxes", return_value=True):
            prices = self.line._thermal_line_prices()
        self.assertAlmostEqual(prices["amount"], self.line.price_total)
        self.assertAlmostEqual(prices["price_unit"] * 2.0 * 0.9, self.line.price_total)
        self.assertEqual(prices["discount"], 10.0)

    def test_line_prices_tax_included_zero_quantity(self):
        self.line.quantity = 0.0
        with patch.object(type(self.invoice), "_thermal_prices_include_taxes", return_value=True):
            self.assertEqual(self.line._thermal_line_prices()["price_unit"], 0.0)

    def test_header_partner_is_company(self):
        self.assertEqual(self.invoice._get_thermal_header_partner(), self.invoice.company_id.partner_id)

    def test_header_logo_placeholder_skipped(self):
        self.assertTrue(self.company_data["company"].uses_default_logo)
        self.assertFalse(bool(self.invoice._get_thermal_header_logo()), "a logo was returned")

    def test_header_logo_company(self):
        self.invoice.company_id.logo = PNG
        self.assertSameImage(self.invoice._get_thermal_header_logo(), self.invoice.company_id.partner_id.image_1920)

    def test_header_logo_from_header_partner(self):
        partner = self.env["res.partner"].create({"name": "Point of sale", "image_1920": PNG})
        with patch.object(type(self.invoice), "_get_thermal_header_partner", return_value=partner):
            self.assertSameImage(self.invoice._get_thermal_header_logo(), partner.image_1920)

    def test_show_company_default(self):
        self.assertTrue(self.env.company.thermal_ticket_show_company)

    def test_current_time_format(self):
        value = self.invoice.get_current_time_formatted()
        self.assertRegex(value, r"^\d{2}:\d{2}$")

    def _render(self):
        self.invoice.action_post()
        html, _ = self.env["ir.actions.report"]._render_qweb_html(REPORT, self.invoice.ids)
        return self._text(html)

    def test_render_generic(self):
        html = self._render()
        self.assertTicketHas(self.invoice.name, html)
        self.assertTicketHas("Thermal product", html)
        self.assertTicketHas(self.tax.tax_group_id.name, html)
        self.assertTicketHas("10.0% desc.", html)

    def test_render_without_company_header(self):
        self.invoice.company_id.thermal_ticket_show_company = False
        html = self._render()
        self.assertTicketHas('name="div_logo"', html, present=False)
        self.assertTicketHas("div_footer_phone", html, present=False)

    def test_render_tax_included_hides_breakdown(self):
        with patch.object(type(self.invoice), "_thermal_prices_include_taxes", return_value=True):
            html = self._render()
        self.assertTicketHas(f"{self.tax.tax_group_id.name}:", html, present=False)
        self.assertTicketHas('name="row_amount_untaxed"', html, present=False)

    def test_render_credit_note_shows_origin(self):
        self.invoice.action_post()
        refund = self.invoice._reverse_moves([{"invoice_date": fields.Date.today()}])
        refund.action_post()
        html, _ = self.env["ir.actions.report"]._render_qweb_html(REPORT, refund.ids)
        self.assertTicketHas(self.invoice.name, self._text(html))
