##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):

    _inherit = "account.move"


    def _compute_tax_totals(self):
        """ Computed field used for custom widget's rendering.
            Only set on invoices.
        """
        for move in self:
            super(AccountMove, move.with_context(
                tax_list_origin=move._origin.mapped('invoice_line_ids.tax_ids'),
                tax_total_origin=move._origin.tax_totals)
            )._compute_tax_totals()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        res = super().copy(default)

        if res.move_type in ['in_refund', 'in_invoice']:
            res.tax_totals = self.tax_totals

        return res
