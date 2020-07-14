##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class AccountCommissionRule(models.Model):

    _inherit = 'account.commission.rule'

    public_category_id = fields.Many2one(
        'product.public.category',
        'Website Category',
        auto_join=True,
    )

    def _get_rule_domain(
            self, date, product, partner_id, customer, amount, analytic_acc):
        domain = super()._get_rule_domain(
            date, product, partner_id, customer, amount, analytic_acc)
        if not product:
            domain += [('public_category_id', '=', False)]
        else:
            domain += [
                '|',
                ('public_category_id', '=', False),
                ('public_category_id', 'parent_of',
                    product.public_categ_ids.ids),
            ]
        return domain
