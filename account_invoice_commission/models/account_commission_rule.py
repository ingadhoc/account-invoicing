##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class AccountCommissionRule(models.Model):

    _name = 'account.commission.rule'
    _order = 'sequence'
    _description = 'Account Commission Rule'

    sequence = fields.Integer(
        'Sequence',
        required=True,
        default=10,
        help="Gives the order in which the rules items will be checked. "
        "The evaluation gives highest priority to lowest sequence and stops "
        "as soon as a matching item is found."
    )
    date_start = fields.Date(
        'Start Date',
        help="Starting date for this rule",
    )
    date_end = fields.Date(
        'End Date',
        help="Ending valid for this rule"
    )
    partner_id = fields.Many2one(
        'res.partner',
        ondelete='cascade',
        auto_join=True,
    )
    customer_id = fields.Many2one(
        'res.partner',
        auto_join=True,
        ondelete='cascade',
        context={'res_partner_search_mode': 'customer'},
    )
    # con prod template ya esta bien, no hace falta product
    product_tmpl_id = fields.Many2one(
        'product.template',
        'Product Template',
        auto_join=True,
        ondelete='cascade',
        help="Specify a template if this rule only applies to one product "
        "template. Keep empty otherwise."
    )
    categ_id = fields.Many2one(
        'product.category',
        'Product Category',
        auto_join=True,
        ondelete='cascade',
        help="Specify a product category if this rule only applies to "
        "products belonging to this category or its children categories. "
        "Keep empty otherwise."
    )
    min_amount = fields.Float(
        help='Minimun Amount on company currency of the invoice to be '
        'evaluated',
        default=0.0,
    )
    percent_commission = fields.Float(
        'Percentage Commission'
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
    )

    def _get_rule_domain(self, date, product, partner_id, customer, amount,
                         analytic_acc):
        domain = [
            '|',
            ('date_start', '=', False),
            ('date_start', '<=', date),
            '|',
            ('analytic_account_id', '=', False),
            ('analytic_account_id', '=', analytic_acc.id),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', date),
            '|',
            ('min_amount', '=', 0.0),
            ('min_amount', '<=', amount),
            ('partner_id', 'in', [False, partner_id]),
            ('customer_id', 'in', [False, customer.id]),
        ]
        # para lineas sin producto buscamos solamente las de false
        if not product:
            domain += [
                ('product_tmpl_id', '=', False), ('categ_id', '=', False)]
        else:
            domain += [
                ('product_tmpl_id', 'in', [False, product.product_tmpl_id.id]),
                '|',
                ('categ_id', '=', False),
                ('categ_id', 'parent_of', product.categ_id.id),
            ]
        return domain

    def _get_rule(self, date, product, partner_id, customer, amount,
                  analytic_acc):
        domain = self._get_rule_domain(
            date, product, partner_id, customer, amount, analytic_acc)
        res = self.search(domain, limit=1)
        if not res:
            if product:
                msj = (_(
                    'No commission rule found for product id "%s", partner id "%s"'
                    ' date "%s" and customer "%s"') % (
                        ' - '.join([str(product.id), product.name]),
                        partner_id,
                        date,
                        ' - '.join([str(customer.id), customer.name])
                    ))
            else:
                msj = (_(
                    'No commission rule found partner id "%s"'
                    ' date "%s" and customer "%s"') % (
                        partner_id,
                        date,
                        ' - '.join([str(customer.id), customer.name])
                    ))
            raise ValidationError(msj)
        return res
