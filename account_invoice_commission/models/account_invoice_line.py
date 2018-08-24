##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    commission_amount = fields.Monetary(
        compute='_compute_commission_amount',
        currency_field='company_currency_id',
    )

    def _compute_commission_amount(self):
        commissioned_partner_id = self._context.get('commissioned_partner_id')
        if commissioned_partner_id:
            today = fields.Date.context_today(self)
            rules = self.env['account.commission.rule']
            _logger.info('Computing commission amount line')
            for rec in self:
                date = rec.invoice_id.date_invoice or today
                rec.commission_amount = rules._get_rule(
                    date, rec.product_id, commissioned_partner_id,
                    rec.invoice_id.commercial_partner_id,
                    rec.price_subtotal_signed,
                    rec.account_analytic_id,
                ).percent_commission * rec.price_subtotal_signed / 100.0
