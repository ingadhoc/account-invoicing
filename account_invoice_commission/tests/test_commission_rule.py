##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from dateutil.relativedelta import relativedelta
from odoo.tests import tagged

from .common import CommissionCommon


@tagged("post_install", "-at_install")
class TestCommissionRule(CommissionCommon):
    def _get_rule(self, product=None, amount=1000.0, account_id=False, date=None):
        return self.env["account.commission.rule"]._get_rule(
            date or self.today,
            self.commissioned_product if product is None else product,
            self.agent.id,
            self.customer,
            amount,
            account_id,
        )

    def test_commission_rule_matching(self):
        """Dado un conjunto de reglas de comisión, cuando se busca la que aplica a una línea,
        entonces gana la primera por secuencia entre las que cumplen fecha, monto, agente,
        cliente, producto, categoría y cuenta.

        Cubre los comportamientos de `_get_rule_domain` / `_get_rule`.
        """
        with self.subTest("gana la de menor secuencia"):
            first, _second = self._rules(
                {"sequence": 5, "percent_commission": 5.0},
                {"sequence": 10, "percent_commission": 10.0},
            )
            self.assertEqual(self._get_rule(), first)

        with self.subTest("la regla sin fechas aplica siempre"):
            always = self._rules({})
            self.assertEqual(self._get_rule(date=self.today + relativedelta(years=3)), always)

        with self.subTest("fuera de la ventana de fechas no aplica"):
            self._rules({"date_start": self.today + relativedelta(days=1)})
            self.assertFalse(self._get_rule())
            self._rules({"date_end": self.today - relativedelta(days=1)})
            self.assertFalse(self._get_rule())

        with self.subTest("por debajo del mínimo no aplica"):
            minimum = self._rules({"min_amount": 1000.0})
            self.assertFalse(self._get_rule(amount=500.0))
            self.assertEqual(self._get_rule(amount=1000.0), minimum)

        with self.subTest("la regla de categoría alcanza a la hija"):
            by_categ = self._rules({"categ_id": self.categ_parent.id})
            self.assertEqual(self._get_rule(), by_categ)

        with self.subTest("una línea sin producto solo toma reglas sin producto ni categoría"):
            self._rules({"categ_id": self.categ_parent.id})
            self.assertFalse(self._get_rule(product=False))

        with self.subTest("la regla de otro agente no aplica"):
            self._rules({"partner_id": self.customer.id})
            self.assertFalse(self._get_rule())

        with self.subTest("la regla de otro cliente no aplica"):
            self._rules({"customer_id": self.agent.id})
            self.assertFalse(self._get_rule())

        with self.subTest("la regla de otra cuenta no aplica"):
            revenue = self.company_data["default_account_revenue"]
            expense = self.company_data["default_account_expense"]
            by_account = self._rules({"account_id": revenue.id})
            self.assertFalse(self._get_rule(account_id=expense.id))
            self.assertEqual(self._get_rule(account_id=revenue.id), by_account)
