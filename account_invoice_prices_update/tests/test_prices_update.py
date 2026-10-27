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
        cls.tax_excluded = cls.env["account.tax"].create(
            {"name": "VAT 21% excluded", "price_include_override": "tax_excluded", **tax_vals}
        )
        cls.tax_included = cls.env["account.tax"].create(
            {"name": "VAT 21% included", "price_include_override": "tax_included", **tax_vals}
        )
        cls.tax_by_document = cls.env["account.tax"].create({"name": "VAT 21%", **tax_vals})
        cls.fiscal_position = cls.env["account.fiscal.position"].create({"name": "Reduced VAT"})
        cls.tax_reduced = cls.env["account.tax"].create(
            {
                **tax_vals,
                "name": "VAT 10.5%",
                "amount": 10.5,
                "fiscal_position_ids": [(6, 0, cls.fiscal_position.ids)],
                "original_tax_ids": [(6, 0, cls.tax_by_document.ids)],
            }
        )

    def _pricelist(self, **rule_vals):
        return self.env["product.pricelist"].create(
            {
                "name": "Prices update pricelist",
                "currency_id": self.company_data["currency"].id,
                "item_ids": [(0, 0, {"applied_on": "3_global", **rule_vals})],
            }
        )

    def _update_prices(
        self, pricelist, product_taxes=None, line_taxes=None, document_tax_mode="tax_excluded", fiscal_position=None
    ):
        self.product.taxes_id = product_taxes or self.tax_excluded
        invoice = self.init_invoice("out_invoice", products=self.product, taxes=line_taxes or self.tax_excluded)
        invoice.document_tax_mode = document_tax_mode
        if fiscal_position:
            invoice.fiscal_position_id = fiscal_position
            invoice.invoice_line_ids.tax_ids = line_taxes
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
        the pricelist price: the base price plus the discount for a plain discount rule, and the
        final price without discount for any other rule."""
        cases = [
            ("a plain discount rule keeps the base price and the discount", {"compute_price": "discount", "price_discount": 10.0}, 100.0, 10.0),
            ("a discount rule with rounding gives the final price", {"compute_price": "discount", "base": "list_price", "price_discount": 12.0, "price_round": 5.0}, 90.0, 0.0),
            ("a fixed price rule gives the fixed price", {"compute_price": "fixed", "fixed_price": 70.0}, 70.0, 0.0),
            ("a surcharge rule gives the final price", {"compute_price": "markup", "base": "list_price", "price_markup": 10.0}, 110.0, 0.0),
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

    def test_update_prices_document_tax_mode(self):
        """Given an invoice in tax excluded or tax included mode, with or without a fiscal position,
        when the wizard applies a pricelist, then the line price is the one of a native invoice
        line: in the invoice tax mode and moved from the product tax to the line tax, with the
        discount apart."""
        fixed = {"compute_price": "fixed", "fixed_price": 121.0}
        discount = {"compute_price": "discount", "price_discount": 10.0}
        cases = [
            ("tax_excluded", False, fixed, 121.0, 0.0),
            ("tax_included", False, fixed, 146.41, 0.0),
            ("tax_included", False, discount, 121.0, 10.0),
            ("tax_included", True, fixed, 133.705, 0.0),
            ("tax_included", True, discount, 110.5, 10.0),
        ]  # fmt: skip
        for document_tax_mode, with_fiscal_position, rule_vals, price_unit, discount_pct in cases:
            label = (
                f"{document_tax_mode} {rule_vals['compute_price']}{' fiscal position' if with_fiscal_position else ''}"
            )
            with self.subTest(label):
                pricelist = self._pricelist(**rule_vals)
                invoice = self._update_prices(
                    pricelist,
                    product_taxes=self.tax_by_document,
                    line_taxes=self.tax_reduced if with_fiscal_position else self.tax_by_document,
                    document_tax_mode=document_tax_mode,
                    fiscal_position=with_fiscal_position and self.fiscal_position,
                )
                self.assert_prices(invoice, pricelist, price_unit, discount_pct)
