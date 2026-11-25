# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _thermal_line_prices(self):
        """Return the unit price, the amount and the discount the receipt prints.

        The unit price is the one before the discount, so the discount can be
        shown next to it; the amount is what the line adds to the total. Both
        follow `_thermal_prices_include_taxes()`, so they are either net or
        tax-included together and the receipt never mixes the two.
        """
        self.ensure_one()
        if not self.move_id._thermal_prices_include_taxes():
            return {"price_unit": self.price_unit, "amount": self.price_subtotal, "discount": self.discount}
        amount = self.price_total
        charged = self.quantity * (1 - (self.discount or 0.0) / 100.0)
        return {
            "price_unit": amount / charged if charged else 0.0,
            "amount": amount,
            "discount": self.discount,
        }
