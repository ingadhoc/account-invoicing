##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api


class AccountChangeCurrency(models.TransientModel):
    _inherit = 'account.change.currency'

    save_secondary_currency = fields.Boolean('Save in secondary currency?')

    same_currency = fields.Boolean(compute='_compute_same_currency')

    currency_company_id = fields.Many2one(
        'res.currency',
        related='invoice_id.company_id.currency_id'
    )

    @api.depends('currency_company_id', 'currency_to_id')
    def _compute_same_currency(self):
        if self.currency_company_id == self.currency_to_id:
            self.same_currency = True

    @api.multi
    def change_currency(self):
        # We set it false because if you change the currency to
        # the same as the secondary currency they can not be the same
        if self.invoice_id.move_currency_id == self.currency_to_id:
            self.invoice_id.move_currency_id = False
            self.invoice_id.move_inverse_currency_rate = False
        currency_from_id = self.currency_from_id
        res = super().change_currency()
        if self.save_secondary_currency and self.same_currency and \
                self.change_type == 'value':
            self.invoice_id.move_currency_id = currency_from_id.id
            self.invoice_id.move_inverse_currency_rate = self.currency_rate
        return res
