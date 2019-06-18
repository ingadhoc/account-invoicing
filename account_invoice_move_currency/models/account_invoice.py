##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    move_currency_id = fields.Many2one(
        'res.currency',
        'Secondary Currency',
        help='If you set a currency here, then this invoice values will be '
        'also stored in the related Account Move Secondary Currency',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    # TODO implement this
    # move_currency_rate = fields.Float(
    move_inverse_currency_rate = fields.Float(
        digits=(16, 4),
        string='Account Move Secondary Currency Rate',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.depends(
        # 'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        # 'move_id.line_ids.amount_residual',
        # 'move_id.line_ids.currency_id'
        'move_currency_id'
    )
    def _compute_residual(self):
        """
        Arreglamos que odoo nos convierte la deuda del asiento, expresada
        en otra moneda, a pesos que es lo que tenemos en la factura.
        Modificamos para que no lo convierta y muestre deuda en pesos si hay
        secondary currency
        """
        for rec in self:
            if not rec.move_currency_id:
                super(AccountInvoice, self)._compute_residual()
                continue

            # si tenemos secondary currency no lo convertimos, mostramos
            # la deuda en moneda de cia
            residual = 0.0
            residual_company_signed = 0.0
            sign = rec.type in ['in_refund', 'out_refund'] and -1 or 1
            for line in rec.sudo().move_id.line_ids.filtered(
                    lambda x: x.account_id.internal_type
                    in ('receivable', 'payable')):
                residual_company_signed += line.amount_residual
                residual += line.amount_residual
            rec.update(
                {'residual_company_signed': abs(
                    residual_company_signed) * sign,
                 'residual_signed': abs(residual) * sign,
                 'residual': abs(residual),
                 'reconciled': True if float_is_zero(
                    abs(residual),
                    precision_rounding=rec.currency_id.rounding) else False})

    @api.onchange('move_currency_id')
    def change_move_currency(self):
        if not self.move_currency_id:
            self.move_inverse_currency_rate = False
        else:
            currency = self.move_currency_id.with_context(
                company_id=self.company_id.id,
                date=self.date_invoice or fields.Date.context_today(self))
            self.move_inverse_currency_rate = currency.compute(
                1.0, self.company_id.currency_id)

    @api.multi
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

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ finalize_invoice_move_lines(move_lines) -> move_lines

            Odoo Hook method to be overridden in additional modules to verify
            and possibly alter the move lines to be created by an invoice, for
            special cases.
            :param move_lines: list of dictionaries with the account.move.lines
                (as for create())
            :return: the (possibly updated) final move_lines to create for this
                invoice
        """
        self.ensure_one()
        move_lines = super(
            AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        if self.move_currency_id:
            if not self.move_inverse_currency_rate:
                raise UserError(_(
                    'If Secondary currency select you must set rate'))
            for a, b, line in move_lines:
                amount = line['debit'] if line['debit'] else line['credit']
                sign = 1.0 if line['debit'] else -1.0
                line['currency_id'] = self.move_currency_id.id
                line['amount_currency'] = sign * self.move_currency_id.round(
                    amount / self.move_inverse_currency_rate)
        return move_lines
