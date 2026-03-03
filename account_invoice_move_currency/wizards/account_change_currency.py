from odoo import api, fields, models


class AccountChangeCurrency(models.TransientModel):
    _inherit = "account.change.currency"

    save_secondary_currency = fields.Boolean("Save in secondary currency?")
    same_currency = fields.Boolean(compute="_compute_same_currency")
    currency_company_id = fields.Many2one("res.currency", related="move_id.company_id.currency_id", store=True)

    @api.depends("currency_company_id", "currency_to_id")
    def _compute_same_currency(self):
        for rec in self:
            if rec.currency_company_id == rec.currency_to_id:
                rec.same_currency = True
            else:
                rec.same_currency = False

    def change_currency(self):
        # We set it false because if you change the currency to
        # the same as the secondary currency they can not be the same
        if self.move_id.move_currency_id == self.currency_to_id:
            self.move_id.move_currency_id = False
            self.move_id.move_inverse_currency_rate = False
        currency_from_id = self.currency_from_id
        res = super().change_currency()
        if self.save_secondary_currency and self.same_currency:
            self.move_id.move_currency_id = currency_from_id.id
            self.move_id.move_inverse_currency_rate = self.conversion_rate
        return res
