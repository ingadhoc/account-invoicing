##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import Command
from odoo.tests import tagged

from .common import CommissionCommon


@tagged("post_install", "-at_install")
class TestCommissionAmount(CommissionCommon):
    def test_commission_amount(self):
        """Dada una factura de cliente alcanzada por una regla al 10%, cuando se la lee con el
        agente en el contexto, entonces cada línea comisiona el 10% de su importe y la factura
        de comisión lo ve a través de `web_read`.

        Cubre el cálculo de `commission_amount` en línea y en factura, y la propagación del
        contexto que hace el override de `web_read`.
        """
        self._rules({"percent_commission": 10.0})
        invoice = self._create_invoice_one_line(
            move_type="out_invoice",
            partner_id=self.customer,
            product_id=self.commissioned_product,
            price_unit=1000.0,
            invoice_date=self.today,
            post=True,
        )
        commission_invoice = self._create_invoice_one_line(
            move_type="in_invoice",
            partner_id=self.agent,
            product_id=self.commissioned_product,
            price_unit=100.0,
            invoice_date=self.today,
            commissioned_invoice_ids=[Command.set(invoice.ids)],
        )

        with self.subTest("la comisión de la línea es el porcentaje del importe"):
            self.env.invalidate_all()
            line = invoice.with_context(commissioned_partner_id=self.agent.id).invoice_line_ids
            self.assertAlmostEqual(line.commission_amount, 100.0)

        with self.subTest("sin regla que aplique la comisión es cero"):
            self._rules({"min_amount": 10000.0})
            self.env.invalidate_all()
            line = invoice.with_context(commissioned_partner_id=self.agent.id).invoice_line_ids
            self.assertAlmostEqual(line.commission_amount, 0.0)

        with self.subTest("web_read propaga el agente a las facturas comisionadas"):
            self._rules({"percent_commission": 10.0})
            self.env.invalidate_all()
            result = commission_invoice.web_read(
                {
                    "partner_id": {"fields": {"display_name": {}}},
                    "commissioned_invoice_ids": {"fields": {"commission_amount": {}}},
                }
            )
            commissioned = result[0]["commissioned_invoice_ids"]
            self.assertEqual(len(commissioned), 1)
            self.assertAlmostEqual(commissioned[0]["commission_amount"], 100.0)

        self.assert_commission_invariants(invoice | commission_invoice, self.agent)
