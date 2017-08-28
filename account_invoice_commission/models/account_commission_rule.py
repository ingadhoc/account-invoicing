# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountCommissionRule(models.Model):

    _name = 'account.commission.rule'
    _order = 'sequence'

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
    )
    customer_id = fields.Many2one(
        'res.partner',
        ondelete='cascade',
        domain=[('customer', '=', True)],
        context={'default_customer': True},
    )
    # con prod template ya esta bien, no hace falta product
    product_tmpl_id = fields.Many2one(
        'product.template',
        'Product Template',
        ondelete='cascade',
        help="Specify a template if this rule only applies to one product "
        "template. Keep empty otherwise."
    )
    categ_id = fields.Many2one(
        'product.category',
        'Product Category',
        ondelete='cascade',
        help="Specify a product category if this rule only applies to "
        "products belonging to this category or its children categories. "
        "Keep empty otherwise."
    )
    percent_commission = fields.Float(
        'Percentage Commission'
    )
    # TODO
    # Por ahora no implementamos ya que habria que tener en cuenta monedas, si
    # incluye o no impuestos y demas, lo dejamos para mas adelante y que
    # alguien lo pague
    # min_amount = fields.Float(
    # )

    @api.model
    def _get_rule(self, date, product, partner_id, customer):
        domain = [
            '|',
            ('date_start', '=', False),
            ('date_start', '<=', date),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', date),
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
        res = self.search(domain, limit=1)
        if not res:
            raise ValidationError(_(
                'No commission rule found for product id "%s", partner id "%s"'
                ' date "%s" and customer "%s"') % (
                product.id, partner_id, date, customer.id))
        return res
