##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from dateutil.relativedelta import relativedelta
from odoo import Command
from odoo.tests import tagged

from .common import CommissionCommon


@tagged("post_install", "-at_install")
class TestAccountMove(CommissionCommon):
    def test_date_last_payment(self):
        """Dada una factura de cliente publicada, cuando se concilia un pago, entonces
        `date_last_payment` queda en la fecha de ese pago, y vuelve a vacío si la conciliación
        se rompe.
        """
        invoice = self._create_invoice_one_line(
            move_type="out_invoice",
            partner_id=self.customer,
            product_id=self.commissioned_product,
            price_unit=1000.0,
            invoice_date=self.today,
            post=True,
        )

        with self.subTest("publicada sin pago no tiene fecha de último pago"):
            self.assertFalse(invoice.date_last_payment)

        payment_date = self.today - relativedelta(days=5)
        with self.subTest("el pago conciliado deja su fecha"):
            self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=invoice.ids
            ).create({"payment_date": payment_date})._create_payments()
            self.assertEqual(invoice.date_last_payment, payment_date)

        with self.subTest("al romper la conciliación la fecha se va"):
            invoice.line_ids.remove_move_reconcile()
            self.assertFalse(invoice.date_last_payment)

    def test_duplicate_reference_bypass(self):
        """Dadas dos facturas de proveedor con la misma referencia, cuando una comisiona
        facturas de cliente, entonces deja de contarse como referencia duplicada.
        """
        invoice = self._create_invoice_one_line(
            move_type="out_invoice",
            partner_id=self.customer,
            product_id=self.commissioned_product,
            price_unit=1000.0,
            invoice_date=self.today,
            post=True,
        )
        bill, twin = (
            self._create_invoice_one_line(
                move_type="in_invoice",
                partner_id=self.agent,
                product_id=self.commissioned_product,
                price_unit=100.0,
                invoice_date=self.today,
                ref="COMM-001",
            )
            for _index in range(2)
        )

        with self.subTest("dos facturas de proveedor con la misma referencia se detectan duplicadas"):
            self.assertTrue(twin._fetch_duplicate_reference())

        with self.subTest("la que comisiona facturas de cliente no dispara el aviso"):
            twin.commissioned_invoice_ids = [Command.set(invoice.ids)]
            self.assertFalse(twin._fetch_duplicate_reference())

        with self.subTest("la otra sigue avisando"):
            self.assertTrue(bill._fetch_duplicate_reference())

        self.assert_commission_invariants(invoice | bill | twin, self.agent)
