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
            invoice = self.env['account.move'].browse(invoice_id)
            return invoice.partner_id.property_product_pricelist

    def update_prices(self):
        self.ensure_one()
        active_id = self._context.get('active_id', False)
        invoice = self.env['account.move'].browse(active_id)
        invoice.write({'currency_id': self.pricelist_id.currency_id.id})
        for line in invoice.invoice_line_ids.filtered('product_id').with_context(check_move_validity=False):
            price, discount = self._get_price_discount(self.pricelist_id, line)
            line.write({
                'price_unit': price,
                'discount': discount,
            })
        invoice.message_post(body='The pricelist is now: %s' % self.pricelist_id.display_name)
        return True

    def _calculate_discount(self, base_price, final_price):
        discount = (base_price - final_price) / base_price * 100
        if (discount < 0 and base_price > 0) or (discount > 0 and base_price < 0):
            discount = 0.0
        return discount

    def _get_price_discount(self, pricelist, invoice_line):
        price_unit = 0.0
        move = invoice_line.move_id
        product = invoice_line.product_id
        uom = invoice_line.product_uom_id
        qty = invoice_line.quantity or 1.0
        date = move.invoice_date or fields.Date.today()
        (final_price, rule_id,) = pricelist._get_product_price_rule(
            product,
            qty,
            uom=uom,
            date=date,
        )
        if pricelist.discount_policy == "with_discount":
            price_unit = self.env["account.tax"]._fix_tax_included_price_company(
                final_price,
                product.taxes_id,
                invoice_line.tax_ids,
                invoice_line.company_id,
            )
            # self.with_context(check_move_validity=False).discount = 0.0
            return price_unit, 0.0
        else:
            rule_id = self.env["product.pricelist.item"].browse(rule_id)
            while (
                rule_id.base == "pricelist"
                and rule_id.base_pricelist_id.discount_policy == "without_discount"
            ):
                new_rule_id = rule_id.base_pricelist_id._get_product_rule(
                    product, qty, uom=uom, date=date
                )
                rule_id = self.env["product.pricelist.item"].browse(new_rule_id)
            base_price = rule_id._compute_base_price(
                product,
                qty,
                uom,
                date,
                currency=invoice_line.currency_id,
            )
            price_unit = max(base_price, final_price)
        return price_unit, self._calculate_discount(base_price, final_price)
