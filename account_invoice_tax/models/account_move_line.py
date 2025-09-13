from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_fixed_amount = fields.Float()
    tax_fixed_amount_in_currency = fields.Float()
