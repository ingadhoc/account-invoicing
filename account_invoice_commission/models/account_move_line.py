##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

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
                date = rec.move_id.invoice_date or today
                rec.commission_amount = rules._get_rule(
                    date, rec.product_id, commissioned_partner_id,
                    rec.move_id.commercial_partner_id,
                    -rec.balance,
                    rec.analytic_account_id,
                ).percent_commission * -rec.balance / 100.0
        else:
            self.commission_amount = 0.0
