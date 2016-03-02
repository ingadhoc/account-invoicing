# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import fields, models, api
import openerp.addons.decimal_precision as dp


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def product_id_change(
            self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False,
            currency_id=False, company_id=None):
        res = super(account_invoice_line, self).product_id_change(
            product, uom_id, qty=qty, name=name, type=type,
            partner_id=partner_id, fposition_id=fposition_id,
            price_unit=price_unit, currency_id=currency_id,
            company_id=company_id)
        price_get = self.env['product.product'].browse(product).with_context(
            currency_id=currency_id).price_get()
        if 'value' not in res:
            res['value'] = {}
        res['value']['list_price'] = price_get and price_get[
            product] or False
        return res

    # we add invoice_id on constraint because sometimes lines are created
    # without an invoice so we add this value when we have the invoice and the
    # currency
    @api.one
    @api.constrains('product_id', 'invoice_id')
    def set_list_price(self):
        currency = self.invoice_id.currency_id
        if self.product_id and currency:
            price_get = self.product_id.with_context(
                currency_id=currency.id
                ).price_get()

            self.list_price = price_get and price_get[
                self.product_id.id] or False

    @api.one
    @api.depends(
        'discount',
        'price_unit',
        )
    def _get_discounts(self):
        discount = 0.0
        total_discount = 0.0
        list_price = self.list_price
        discount = list_price and (
            (list_price - self.price_unit) * 100.0 / list_price) or 0.0
        total_discount = discount + self.discount - (
            discount * self.discount or 0.0) / 100.0

        self.list_price = list_price
        self.list_discount = discount
        self.total_discount = total_discount

    @api.one
    def _set_discount(self):
        discount = 0.0
        # if price_unit = 0 then we dont calculate anything
        if self.price_unit:
            total_discount_perc = self.total_discount / 100.0
            list_discount_perc = self.list_discount / 100.0
            discount = 1.0 - (
                (1.0 - total_discount_perc) / (1.0 - list_discount_perc))
        self.discount = discount * 100.0

    list_price = fields.Float(
        digits=dp.get_precision('Account'),
        string='List Price',
        readonly=True
        )
    list_discount = fields.Float(
        compute='_get_discounts',
        string='List Discount'
        )
    total_discount = fields.Float(
        compute='_get_discounts',
        inverse='_set_discount',
        string='Total Discount'
        )
