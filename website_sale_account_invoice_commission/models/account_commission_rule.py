##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class AccountCommissionRule(models.Model):
    _inherit = "account.commission.rule"

    public_category_id = fields.Many2one(
        "product.public.category",
        "Website Category",
        bypass_search_access=True,
    )
    deleted_public_category = fields.Char(
        "Deleted Website Category",
        readonly=True,
        copy=False,
        help="Website category this rule was filtered by, when it was deleted and the rule got archived.",
    )

    def _get_rule_domain(self, date, product, partner_id, customer, amount, account_id=False):
        domain = super()._get_rule_domain(date, product, partner_id, customer, amount, account_id=account_id)
        if not product:
            domain += [("public_category_id", "=", False)]
        else:
            domain += [
                "|",
                ("public_category_id", "=", False),
                ("public_category_id", "parent_of", product.public_categ_ids.ids),
            ]
        return domain
