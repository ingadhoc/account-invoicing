# -*- encoding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError


class account_change_currency(models.TransientModel):
    _name = 'account.change.currency'
    _description = 'Change Currency'

    currency_id = fields.Many2one(
        'res.currency',
        string='Change to',
        required=True,
        help="Select a currency to apply on the invoice"
    )
    currency_rate = fields.Float(
        'Currency Rate',
        required=True,
        help="Select a currency to apply on the invoice"
    )
    currency_rate_readonly = fields.Float(
        related='currency_rate',
        readonly=True,
    )

    @api.multi
    def get_invoice(self):
        self.ensure_one()
        invoice = self.env['account.invoice'].browse(
            self._context.get('active_id', False))
        if not invoice:
            raise ValidationError(_('No Invoice on context as "active_id"'))
        return invoice

    @api.onchange('currency_id')
    def onchange_currency(self):
        invoice = self.get_invoice()
        if not self.currency_id:
            self.currency_rate = False
        else:
            if self.currency_id == invoice.currency_id:
                raise ValidationError(_(
                    'Old Currency And New Currency can not be the same'))
            currency = invoice.currency_id.with_context(
                date=invoice.date_invoice or fields.Date.context_today(self))
            self.currency_rate = currency.compute(
                1.0, self.currency_id)

    @api.multi
    def change_currency(self, ):
        """
        We overwrite original function to simplify and add functionality
        descrived on the manifest
        """
        self.ensure_one()
        invoice = self.get_invoice()
        message = _("Currency changed from %s to %s with rate %s") % (
            invoice.currency_id.name, self.currency_id.name,
             self.currency_rate)
        for line in invoice.invoice_line_ids:
            line.price_unit = self.currency_id.round(
                line.price_unit * self.currency_rate)
        invoice.currency_id = self.currency_id.id

        # update manual taxes
        for line in invoice.tax_line_ids.filtered(lambda x: x.manual):
            line.amount = self.currency_id.round(
                line.amount * self.currency_rate)

        invoice.compute_taxes()
        invoice.message_post(message)
        return {'type': 'ir.actions.act_window_close'}
