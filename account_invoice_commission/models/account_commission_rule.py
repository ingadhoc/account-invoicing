##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models
from odoo.fields import Domain


class AccountCommissionRule(models.Model):
    _name = "account.commission.rule"
    _order = "sequence"
    _description = "Account Commission Rule"

    sequence = fields.Integer(
        required=True,
        default=10,
        help="Gives the order in which the rules items will be checked. "
        "The evaluation gives highest priority to lowest sequence and stops "
        "as soon as a matching item is found.",
    )
    date_start = fields.Date(
        "Start Date",
        help="Starting date for this rule",
    )
    date_end = fields.Date("End Date", help="Ending valid for this rule")
    partner_id = fields.Many2one(
        "res.partner",
        ondelete="cascade",
        bypass_search_access=True,
    )
    customer_id = fields.Many2one(
        "res.partner",
        bypass_search_access=True,
        ondelete="cascade",
        context={"res_partner_search_mode": "customer"},
    )
    # con prod template ya esta bien, no hace falta product
    product_tmpl_id = fields.Many2one(
        "product.template",
        "Product Template",
        bypass_search_access=True,
        ondelete="cascade",
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.",
    )
    categ_id = fields.Many2one(
        "product.category",
        "Product Category",
        bypass_search_access=True,
        ondelete="cascade",
        help="Specify a product category if this rule only applies to "
        "products belonging to this category or its children categories. "
        "Keep empty otherwise.",
    )
    min_amount = fields.Float(
        help="Minimun Amount on company currency of the invoice to be evaluated",
        default=0.0,
    )
    percent_commission = fields.Float("Percentage Commission")
    account_id = fields.Many2one(
        "account.account",
        "Commission Account",
        help="Specify an account if this rule only applies to commission "
        "lines with this account. Keep empty to apply to all accounts.",
    )

    def _get_rule_domain(self, date, product, partner_id, customer, amount, account_id=False):
        # Fecha
        date_start_domain = Domain([("date_start", "<=", date)]) | Domain([("date_start", "=", False)])
        date_end_domain = Domain([("date_end", ">=", date)]) | Domain([("date_end", "=", False)])
        date_domain = date_start_domain & date_end_domain

        # Monto
        amount_domain = Domain([("min_amount", "<=", amount)]) | Domain([("min_amount", "=", 0.0)])

        # Partner / customer
        partner_customer_domain = Domain(
            [
                ("partner_id", "in", [False, partner_id]),
                ("customer_id", "in", [False, customer.id]),
            ]
        )

        # Producto / Categoría
        if not product:
            # Para lineas sin producto buscamos solamente las de false
            product_domain = Domain(
                [
                    ("product_tmpl_id", "=", False),
                    ("categ_id", "=", False),
                ]
            )
        else:
            # Reglas específicas de producto o categoría
            product_tmpl_domain = Domain(
                [
                    ("product_tmpl_id", "in", [False, product.product_tmpl_id.id]),
                ]
            )
            categ_domain = Domain([("categ_id", "=", False)]) | Domain(
                [
                    ("categ_id", "parent_of", product.categ_id.id),
                ]
            )
            product_domain = product_tmpl_domain & categ_domain

        # Dominio final
        final_domain = date_domain & amount_domain & partner_customer_domain & product_domain
        if account_id:
            domain_account = Domain([("account_id", "in", [False, account_id])])
            final_domain = final_domain & domain_account
        return final_domain

    def _get_rule(self, date, product, partner_id, customer, amount, account_id=False):
        domain = self._get_rule_domain(date, product, partner_id, customer, amount, account_id)
        return self.search(domain, limit=1)
