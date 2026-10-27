##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPricesUpdate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls._create_product(name="Prices update product", lst_price=100.0)
        tax_vals = {"amount_type": "percent", "amount": 21.0, "type_tax_use": "sale"}
        cls.tax_excluded = cls.env["account.tax"].create({"name": "VAT 21% excluded", **tax_vals})
        cls.tax_included = cls.env["account.tax"].create(
            {"name": "VAT 21% included", "price_include_override": "tax_included", **tax_vals}
        )

    def _pricelist(self, **rule_vals):
        return self.env["product.pricelist"].create(
            {
                "name": "Prices update pricelist",
                "currency_id": self.company_data["currency"].id,
                "item_ids": [(0, 0, {"applied_on": "3_global", **rule_vals})],
            }
        )

    def _update_prices(self, pricelist, product_taxes=None):
        self.product.taxes_id = product_taxes or self.tax_excluded
        invoice = self.init_invoice("out_invoice", products=self.product, taxes=self.tax_excluded)
        wizard = (
            self.env["account.invoice.prices_update.wizard"]
            .with_context(active_id=invoice.id)
            .create({"pricelist_id": pricelist.id})
        )
        wizard.update_prices()
        return invoice

    def assert_prices(self, invoice, pricelist, price_unit, discount):
        line = invoice.invoice_line_ids
        self.assertRecordValues(line, [{"price_unit": price_unit, "discount": discount}])
        self.assertEqual(invoice.currency_id, pricelist.currency_id)
        self.assertIn(pricelist.display_name, invoice.message_ids[0].body)

    def test_update_prices_by_rule_type(self):
        """Given a draft customer invoice, when the wizard applies a pricelist, then each line gets
        the pricelist price: the base price plus the discount for a plain percentage rule, and the
        final price without discount for any other rule."""
        cases = [
            ("a percentage rule keeps the base price and the discount", {"compute_price": "percentage", "percent_price": 10.0}, 100.0, 10.0),
            ("a formula rule with rounding gives the final price", {"compute_price": "formula", "base": "list_price", "price_discount": 12.0, "price_round": 5.0}, 90.0, 0.0),
            ("a fixed price rule gives the fixed price", {"compute_price": "fixed", "fixed_price": 70.0}, 70.0, 0.0),
            ("a formula surcharge gives the final price", {"compute_price": "formula", "base": "list_price", "price_discount": -10.0}, 110.0, 0.0),
        ]  # fmt: skip
        for label, rule_vals, price_unit, discount in cases:
            with self.subTest(label):
                pricelist = self._pricelist(**rule_vals)
                invoice = self._update_prices(pricelist)
                self.assert_prices(invoice, pricelist, price_unit, discount)

    def test_update_prices_tax_included_product(self):
        """Given a product with a tax included price and an invoice line with the tax excluded,
        when the wizard applies a fixed price, then the line gets the price without the tax."""
        pricelist = self._pricelist(compute_price="fixed", fixed_price=121.0)
        invoice = self._update_prices(pricelist, product_taxes=self.tax_included)
        self.assert_prices(invoice, pricelist, 100.0, 0.0)
