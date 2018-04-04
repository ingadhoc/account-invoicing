##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    commission_amount = fields.Monetary(
        compute='_compute_commission_amount',
        currency_field='company_currency_id',
    )
    commission_invoice_ids = fields.Many2many(
        'account.invoice',
        'account_invoice_commission_inv_rel',
        'commissioned_id',
        'commission_id',
        string='Commission Invoices',
        domain=[('type', 'in', ('in_invoice', 'in_refund'))],
        readonly=True,
        help='Commision invoices where this invoice is commissioned',
        copy=False,
    )
    commissioned_invoice_ids = fields.Many2many(
        'account.invoice',
        'account_invoice_commission_inv_rel',
        'commission_id',
        'commissioned_id',
        # 'commission_invoice_id',
        domain=[('type', 'in', ('out_invoice', 'out_refund'))],
        string='Commissioned invoices',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='The invoices that this commission invoice is commissioning',
        copy=False,
    )
    # este campo lo agregamos aca y no en account_usability para no perjudicar
    # a quien no usa comisiones en temas de performance
    date_last_payment = fields.Date(
        compute='_compute_date_last_payment',
        string='Last Payment Date',
        store=True,
    )
    partner_user_id = fields.Many2one(
        'res.users',
        compute='_compute_partner_user',
    )

    @api.depends('partner_id.user_ids')
    def _compute_partner_user(self):
        for rec in self:
            users = rec.partner_id.user_ids
            rec.partner_user_id = users and users[0] or False

    @api.depends('payment_move_line_ids.date')
    def _compute_date_last_payment(self):
        for rec in self:
            rec.date_last_payment = rec.payment_move_line_ids and \
                rec.payment_move_line_ids[0].date

    @api.depends('invoice_line_ids.commission_amount')
    def _compute_commission_amount(self):
        commissioned_partner_id = self._context.get('commissioned_partner_id')
        if commissioned_partner_id:
            _logger.info('Computing commission amount')
            for rec in self:
                rec.commission_amount = sum(
                    rec.mapped('invoice_line_ids.commission_amount'))
