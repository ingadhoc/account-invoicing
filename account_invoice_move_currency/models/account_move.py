##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    move_currency_id = fields.Many2one(
        'res.currency', 'Secondary Currency', readonly=True,
        help='If you set a currency here, then this invoice values will be also stored in the related Account Move Secondary Currency')

    move_inverse_currency_rate = fields.Float(
        digits=(16, 4), string='Account Move Secondary Currency Rate', readonly=True)

    @api.onchange('move_currency_id')
    def change_move_currency(self):
        if not self.move_currency_id:
            self.move_inverse_currency_rate = False
        else:
            self.move_inverse_currency_rate = self.move_currency_id._convert(
                1.0, self.company_id.currency_id, self.company_id, self.invoice_date or fields.Date.context_today(self))

    @api.constrains('move_currency_id', 'currency_id')
    def check_move_currency(self):
        for rec in self.filtered('move_currency_id'):
            if rec.move_currency_id == rec.currency_id:
                raise UserError(_('Secondary currency can not be the same as Invoice Currency'))
            if rec.currency_id != rec.company_id.currency_id:
                raise UserError(_('Can not use Secondary currency if invoice is in a Currency different from Company Currency'))
