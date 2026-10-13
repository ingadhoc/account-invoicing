##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class CommissionInvariants:
    """Batería de invariantes de las facturas de comisión.

    Valen después de cualquier operación del módulo — no son el assert específico de ningún
    escenario. Se corren sobre los registros que creó el test, nunca sobre lo que haya en la base.
    """

    def assert_commission_invariants(self, moves, commissioned_partner):
        self.assert_commission_is_sum_of_lines(moves, commissioned_partner)
        self.assert_no_commission_without_context(moves)
        self.assert_commission_link_is_symmetric(moves)

    def assert_commission_is_sum_of_lines(self, moves, commissioned_partner):
        # La comisión de la factura es la de sus líneas: cualquier otra cosa es un total inventado.
        self.env.invalidate_all()
        for move in moves.with_context(commissioned_partner_id=commissioned_partner.id):
            self.assertAlmostEqual(
                move.commission_amount,
                sum(move.invoice_line_ids.mapped("commission_amount")),
                msg="la comisión de %s no es la suma de sus líneas" % move.id,
            )

    def assert_no_commission_without_context(self, moves):
        # Sin agente en el contexto no hay comisión que calcular: el cálculo es por agente.
        self.env.invalidate_all()
        for move in moves.with_context(commissioned_partner_id=False):
            self.assertEqual(move.commission_amount, 0.0, "%s calculó comisión sin agente" % move.id)
            for line in move.invoice_line_ids:
                self.assertEqual(line.commission_amount, 0.0, "la línea %s calculó comisión sin agente" % line.id)

    def assert_commission_link_is_symmetric(self, moves):
        # Las dos m2m comparten tabla: si se ven distinto, una de las dos quedó mal declarada.
        for move in moves:
            for commissioned in move.commissioned_invoice_ids:
                self.assertIn(move, commissioned.commission_invoice_ids, "%s no ve a su comisión" % commissioned.id)
            for commission in move.commission_invoice_ids:
                self.assertIn(move, commission.commissioned_invoice_ids, "%s no ve a su comisionada" % commission.id)


class CommissionCommon(AccountTestInvoicingCommon, CommissionInvariants):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # El hoy se congela una vez: las fechas del escenario y de los asserts salen de acá.
        cls.today = fields.Date.today()
        cls.agent = cls.env["res.partner"].create({"name": "commission agent"})
        cls.customer = cls.partner_a
        cls.categ_parent = cls.env["product.category"].create({"name": "commission parent categ"})
        cls.categ_child = cls.env["product.category"].create(
            {"name": "commission child categ", "parent_id": cls.categ_parent.id}
        )
        cls.commissioned_product = cls._create_product(
            name="commissioned product",
            categ_id=cls.categ_child.id,
        )

    def _rules(self, *vals_list):
        """Deja en la base solo las reglas que el escenario necesita."""
        self.env["account.commission.rule"].search([]).unlink()
        values = [dict({"percent_commission": 10.0}, **vals) for vals in vals_list]
        return self.env["account.commission.rule"].create(values)
