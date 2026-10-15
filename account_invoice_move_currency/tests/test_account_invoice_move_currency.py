import lxml.html
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountInvoiceMoveCurrency(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 1 company currency = 2 other currency from 2017 on
        cls.other_currency = cls.setup_other_currency("EUR")
        cls.company_currency = cls.env.company.currency_id

    def _create_test_invoice(self, currency=None):
        return self.init_invoice(
            "out_invoice",
            invoice_date="2017-01-01",
            amounts=[1000.0],
            currency=currency or self.company_currency,
        )

    def _change_currency(self, move, currency_to, rate, save_secondary=False):
        wizard = (
            self.env["account.change.currency"]
            .with_context(active_id=move.id, active_model="account.move")
            .create(
                {
                    "currency_to_id": currency_to.id,
                    "conversion_rate": rate,
                    "save_secondary_currency": save_secondary,
                }
            )
        )
        wizard.change_currency()
        return wizard

    def test_onchange_computes_rate(self):
        move = self._create_test_invoice()
        move.move_currency_id = self.other_currency
        move.change_move_currency()
        self.assertAlmostEqual(move.move_inverse_currency_rate, 0.5)

        move.move_currency_id = False
        move.change_move_currency()
        self.assertFalse(move.move_inverse_currency_rate)

    def test_secondary_currency_same_as_invoice_currency(self):
        move = self._create_test_invoice()
        with self.assertRaises(UserError):
            move.move_currency_id = self.company_currency

    def test_secondary_currency_needs_company_currency_invoice(self):
        move = self._create_test_invoice(currency=self.other_currency)
        with self.assertRaises(UserError):
            move.move_currency_id = self.env.ref("base.ARS")

    def test_change_currency_saves_secondary_currency(self):
        move = self._create_test_invoice(currency=self.other_currency)
        wizard = self._change_currency(move, self.company_currency, 0.5, save_secondary=True)
        self.assertTrue(wizard.same_currency)
        self.assertEqual(move.currency_id, self.company_currency)
        self.assertEqual(move.move_currency_id, self.other_currency)
        self.assertAlmostEqual(move.move_inverse_currency_rate, 0.5)
        self.assertAlmostEqual(move.amount_untaxed, 500.0)

    def test_change_currency_without_saving_secondary_currency(self):
        move = self._create_test_invoice(currency=self.other_currency)
        self._change_currency(move, self.company_currency, 0.5)
        self.assertEqual(move.currency_id, self.company_currency)
        self.assertFalse(move.move_currency_id)

    def test_change_currency_to_secondary_currency_clears_it(self):
        move = self._create_test_invoice()
        move.write({"move_currency_id": self.other_currency.id, "move_inverse_currency_rate": 0.5})
        self._change_currency(move, self.other_currency, 2.0)
        self.assertEqual(move.currency_id, self.other_currency)
        self.assertFalse(move.move_currency_id)
        self.assertFalse(move.move_inverse_currency_rate)

    def test_report_shows_secondary_currency_total(self):
        move = self._create_test_invoice()
        move.write({"move_currency_id": self.other_currency.id, "move_inverse_currency_rate": 0.5})
        move.action_post()
        html = self.env["ir.actions.report"]._render_qweb_html("account.report_invoice", move.ids)[0]
        text = " ".join(lxml.html.fromstring(html).text_content().replace("\xa0", " ").split())
        expected = self.other_currency.format(move.amount_total / 0.5).replace("\xa0", " ")
        self.assertIn(f"El total de este comprobante equivale a un total de {expected}", text)
