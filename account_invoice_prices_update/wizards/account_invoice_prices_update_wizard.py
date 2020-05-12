##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api


class AccountInvoicePricesUpdateWizard(models.TransientModel):
    _name = 'account.invoice.prices_update.wizard'
    _description = 'account.invoice.prices_update.wizard'

    pricelist_id = fields.Many2one(
        'product.pricelist',
        required=True,
        default=lambda self: self._get_pricelist(),
    )

    @api.model
    def _get_pricelist(self):
        invoice_id = self._context.get('active_id', False)
        if invoice_id:
            invoice = self.env['account.invoice'].browse(invoice_id)
            return invoice.partner_id.property_product_pricelist

    @api.multi
    def _get_display_price_and_discount(self, product, line):
        discount = 0.0
        if self.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(
                pricelist=self.pricelist_id.id).price, discount
        partner = line.invoice_id.partner_id
        product_context = dict(
            self.env.context, partner_id=partner.id,
            date=line.invoice_id.date_invoice, uom=line.uom_id.id)
        final_price, rule_id = self.pricelist_id.with_context(
            product_context).get_product_price_rule(
            line.product_id, line.quantity or 1.0, partner)
        base_price, currency_id = self.with_context(
            product_context)._get_real_price_currency(
            product, rule_id, line.quantity, line.uom_id,
            self.pricelist_id.id, partner)
        if currency_id != self.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(
                currency_id).with_context(
                product_context).compute(base_price,
                                         self.pricelist_id.currency_id)
        if final_price != 0:
            discount = (base_price - final_price) / base_price * 100
        return max(base_price, final_price), discount

    @api.multi
    def update_prices(self):
        self.ensure_one()
        active_id = self._context.get('active_id', False)
        invoice = self.env['account.invoice'].browse(active_id)
        invoice.write({'currency_id': self.pricelist_id.currency_id.id})
        for line in invoice.invoice_line_ids.filtered(lambda l: l.product_id and l.product_id.lst_price):
            product = line.product_id.with_context(
                lang=invoice.partner_id.lang,
                partner=invoice.partner_id.id,
                quantity=line.quantity,
                date=invoice.date_invoice,
                pricelist=self.pricelist_id.id,
                uom=line.uom_id.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            price, discount = self._get_display_price_and_discount(
                product, line)

            line.write({
                'price_unit': price,
                'discount': discount,
            })
        invoice.compute_taxes()
        return True

    def _get_real_price_currency(
            self, product, rule_id, qty, uom, pricelist_id, partner):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quantity of product
            :param tuple price_and_rule: tuple(price, suitable_rule)
             coming from pricelist computation
            :param obj uom: unit of measure of current invoice line
            :param integer pricelist_id: pricelist id of invoice
            :param obj partner: partner id of invoice"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.\
                    discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and\
                    pricelist_item.base_pricelist_id and \
                    pricelist_item.base_pricelist_id.\
                        discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.\
                        with_context(
                            uom=uom.id).get_product_price_rule(
                                product, qty, partner)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and\
                    pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(
                    pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(
                    product_currency, currency_id)

        uom_uom = self.env.context.get('uom') or uom.uom_id.id
        if uom and uom.id != uom_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, uom.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id.id
