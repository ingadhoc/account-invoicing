##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import Command, _, fields, models
from odoo.tools import float_round, formatLang


class AccountInvoicePartialWizard(models.TransientModel):
    _name = "account.invoice.partial.wizard"
    _description = "Account Invoice Partial Wizard"

    invoice_id = fields.Many2one(
        "account.move",
        default=lambda x: x._context.get("active_id", False),
    )
    percentage_to_invoice = fields.Float(
        required=True,
    )
    rounding = fields.Float(
        string="Rounding Precision",
        required=True,
        help="Represent the non-zero value smallest coinage" " (for example, 0.05).",
        default=0.01,
    )
    rounding_method = fields.Selection(
        required=True,
        selection=[("UP", "UP"), ("DOWN", "DOWN"), ("HALF-UP", "HALF-UP")],
        default="HALF-UP",
        help="The tie-breaking rule used for float rounding operations",
    )

    def _get_partial_line_vals(self, line):
        """Values to write on ``line``. Hook for modules applying the percentage on another field."""
        return {
            "quantity": float_round(
                line.quantity * (self.percentage_to_invoice / 100),
                precision_rounding=self.rounding,
                rounding_method=self.rounding_method,
            ),
        }

    def _log_partial_invoice(self, amount_before):
        """Log the change on the invoice chatter: the write runs with tracking disabled for performance."""
        invoice = self.invoice_id
        invoice._message_log(
            body=_(
                "Invoice percentage applied: %(percentage)s%%. Total changed from %(before)s to %(after)s.",
                percentage=formatLang(self.env, self.percentage_to_invoice),
                before=formatLang(self.env, amount_before, currency_obj=invoice.currency_id),
                after=formatLang(self.env, invoice.amount_total, currency_obj=invoice.currency_id),
            )
        )

    def compute_new_quantity(self):
        self.ensure_one()
        # One write on the move instead of one assignment per line. Line by line, each assignment is a write
        # that runs the whole dynamic lines sync (taxes, payment terms, discount allocation), and every nested
        # write calls fields_get() in the tracking block of account.move.line.write() -- which, with no tracked
        # field in vals, ends up describing every field of the model. tracking_disable skips that block.
        invoice = self.invoice_id.with_context(check_move_validity=False, tracking_disable=True)
        amount_before = invoice.amount_total
        invoice.write(
            {
                "invoice_line_ids": [
                    Command.update(line.id, self._get_partial_line_vals(line)) for line in invoice.invoice_line_ids
                ],
            }
        )
        # tracking_disable above means the amount change leaves no tracking values, so log it explicitly.
        self._log_partial_invoice(amount_before)
