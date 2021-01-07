##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    move_currency_id = fields.Many2one(
        'res.currency',
        'Secondary Currency',
        help='If you set a currency here, then this invoice values will be '
        'also stored in the related Account Move Secondary Currency',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    move_inverse_currency_rate = fields.Float(
        digits=(16, 4),
        string='Account Move Secondary Currency Rate',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.depends('move_currency_id')
    def _compute_amount(self):
        """
        Arreglamos que odoo nos convierte la deuda del asiento, expresada
        en otra moneda, a pesos que es lo que tenemos en la factura.
        Modificamos para que no lo convierta y muestre deuda en pesos si hay
        secondary currency
        TODO ver si podemos eliminar esto, es horrible
        """
        res = super()._compute_amount()
        for move in self.filtered('move_currency_id'):
            # si tenemos secondary currency no lo convertimos, mostramos
            # la deuda en moneda de cia
            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = sign * -move.amount_untaxed_signed
            move.amount_tax = sign * -move.amount_tax_signed
            move.amount_total = sign * -move.amount_total_signed
            move.amount_residual = -sign * move.amount_residual_signed
        return res

    @api.onchange('move_currency_id')
    def change_move_currency(self):
        if not self.move_currency_id:
            self.move_inverse_currency_rate = False
        else:
            self.move_inverse_currency_rate = self.move_currency_id._convert(
                1.0, self.company_id.currency_id, self.company_id,
                self.invoice_date or fields.Date.context_today(self))

    @api.constrains('move_currency_id', 'currency_id')
    def check_move_currency(self):
        for rec in self.filtered('move_currency_id'):
            if rec.move_currency_id == rec.currency_id:
                raise UserError(_(
                    'Secondary currency can not be the same as Invoice '
                    'Currency'))
            if rec.currency_id != rec.company_id.currency_id:
                raise UserError(_(
                    'Can not use Secondary currency if invoice is in a '
                    'Currency different from Company Currency'))

    def post(self):
        """ para no tener que mandar el move currency en el context o hacer tmb onchanges nos la simpificamos y solo
        lo computamos en el post. Algo similar pasa tambien en odoo nativo, si bien a priroi se setea la currency_id
        (cuando la factura es en otra moneda) se puede forzar que no pase y luego se setea en el post"""
        res = super().post()
        for rec in self.filtered('move_currency_id'):
            if not rec.move_inverse_currency_rate:
                raise UserError(_('If Secondary currency select you must set rate. Check invoice id: %s') % rec.id)
            # only debt lines because if not invoice lines prices are shown on move currency
            for line in rec.line_ids.filtered(
                    lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                amount = line.debit if line.debit else line.credit
                sign = 1.0 if line.debit else -1.0
                line.currency_id = self.move_currency_id.id
                line.amount_currency = sign * self.move_currency_id.round(amount / self.move_inverse_currency_rate)
        return res
