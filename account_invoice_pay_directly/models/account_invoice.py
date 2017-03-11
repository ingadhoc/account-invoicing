# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_reference = fields.Char(
        'Payment Reference',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    pay_now = fields.Selection([
        ('pay_now', 'Pay Directly'),
        ('pay_later', 'Pay Later')],
        'Payment',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default='pay_later'
    )
    payment_account_id = fields.Many2one(
        related='account_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('deprecated', '=', False), "
        "('internal_type','=', 'liquidity'), ('company_id', '=', company_id)]",
    )

    @api.onchange('payment_account_id')
    def change_payment_account(self):
        self.account_id = self.payment_account_id

    @api.onchange('pay_now')
    def change_pay_now(self):
        if self.pay_now == 'pay_now':
            self.payment_account_id = False
            self.payment_term_id = False
            self.date_due = False
        else:
            # set payment termn and account again (backup and restore fiscal
            # position in case user has change it)
            fiscal_position = self.fiscal_position_id
            self._onchange_partner_id()
            self.fiscal_position_id = fiscal_position

    @api.multi
    def action_move_create(self):
        self.check_pay_now()
        return super(AccountInvoice, self).action_move_create()

    @api.multi
    def check_pay_now(self):
        for rec in self:
            if rec.pay_now == 'pay_now':
                if rec.account_id.internal_type != 'liquidity':
                    raise ValidationError(_(
                        'To validate an invoice with "Pay Directly" a '
                        'liquidity account must be selected!'))
            elif rec.account_id.internal_type not in ('receivable', 'payable'):
                raise ValidationError(_(
                    'To validate an invoice with "Pay Later" a receivable or'
                    'payable account must be selected!'))

    @api.multi
    def direct_pay_invoice_cancel(self):
        for rec in self:
            if rec.pay_now == 'pay_now' and rec.state == 'paid':
                rec.action_cancel()
