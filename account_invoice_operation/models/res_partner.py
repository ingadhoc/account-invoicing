# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    default_sale_invoice_plan_id = fields.Many2one(
        'account.invoice.plan',
        'Default Invoice Plan',
        domain=[('type', 'in', ['sale', False])],
        company_dependent=True,
        help='This invoice plan will be automatically loaded on invoices and '
        'sale orders'
    )
