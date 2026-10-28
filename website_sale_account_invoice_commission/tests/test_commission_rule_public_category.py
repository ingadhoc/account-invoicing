##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.addons.account_invoice_commission.tests.common import CommissionCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCommissionRulePublicCategory(CommissionCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PublicCategory = cls.env["product.public.category"]
        cls.public_parent = PublicCategory.create({"name": "commission public parent"})
        cls.public_child = PublicCategory.create({"name": "commission public child", "parent_id": cls.public_parent.id})
        cls.public_other = PublicCategory.create({"name": "commission public other"})
        cls.commissioned_product.public_categ_ids = cls.public_child
        cls.other_product = cls._create_product(
            name="other public categ product", public_categ_ids=cls.public_other.ids
        )

    def _get_rule(self, product):
        return self.env["account.commission.rule"]._get_rule(self.today, product, self.agent.id, self.customer, 1000.0)

    def test_commission_rule_public_category(self):
        """Given commission rules filtered by website category, when looking for the rule of a
        line, then a rule applies to products in that category or its children, and never to
        products of another category or to lines without product.
        """
        with self.subTest("a rule on the parent website category applies to a child category product"):
            by_public_categ = self._rules({"public_category_id": self.public_parent.id})
            self.assertEqual(self._get_rule(self.commissioned_product), by_public_categ)

        with self.subTest("a rule on another website category does not apply"):
            self._rules({"public_category_id": self.public_parent.id})
            self.assertFalse(self._get_rule(self.other_product))

        with self.subTest("a line without product only takes rules without website category"):
            by_public_categ, without_public_categ = self._rules(
                {"sequence": 5, "public_category_id": self.public_parent.id},
                {"sequence": 10},
            )
            self.assertEqual(self._get_rule(False), without_public_categ)
