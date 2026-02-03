##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    user_exchange_rate = fields.Float(
        string="Informative Exchange Rate",
        help="Informative exchange rate value.",
        digits=(16, 2),
        compute="_compute_user_exchange_rate",
        store=True,
    )

    user_secondary_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Secondary Currency",
    )

    @api.depends("user_secondary_currency_id", "invoice_date", "company_id")
    def _compute_user_exchange_rate(self):
        for move in self:
            move.user_exchange_rate = False
            currency = move.user_secondary_currency_id
            date = move.invoice_date

            if currency and date:
                rates_dict = currency._get_rates(move.company_id, date)
                rate = rates_dict.get(currency.id)
                if rate and rate != 0:
                    move.user_exchange_rate = 1 / rate
