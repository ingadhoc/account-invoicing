# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class account_invoice(models.Model):

    _inherit = 'account.invoice'

    order_ids = fields.Many2many(
        'sale.order',
        'sale_order_invoice_rel',
        'invoice_id',
        'order_id')
    purchase_ids = fields.Many2many(
        'purchase.order',
        'purchase_invoice_rel',
        'invoice_id',
        'purchase_id')
