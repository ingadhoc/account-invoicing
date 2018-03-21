# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import fields, models, api


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    sale_order_ids = fields.Many2many(
        'sale.order',
        compute='compute_sale_orders'
    )
    purchase_order_ids = fields.Many2many(
        'purchase.order',
        compute='compute_purchase_orders'
    )

    @api.multi
    def compute_purchase_orders(self):
        for rec in self:
            rec.purchase_order_ids = self.env['purchase.order.line'].search(
                [('invoice_lines', 'in', rec.invoice_line_ids.ids)]).mapped(
                'order_id')

    @api.multi
    def compute_sale_orders(self):
        for rec in self:
            rec.sale_order_ids = self.env['sale.order.line'].search(
                [('invoice_lines', 'in', rec.invoice_line_ids.ids)]).mapped(
                'order_id')
