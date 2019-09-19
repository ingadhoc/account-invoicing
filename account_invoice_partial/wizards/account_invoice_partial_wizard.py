##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
from odoo.tools import float_round


class AccountInvoicePartialWizard(models.TransientModel):

    _name = "account.invoice.partial.wizard"
    _description = "Account Invoice Partial Wizard"

    invoice_id = fields.Many2one(
        'account.invoice',
        default=lambda x: x._context.get('active_id', False),
    )
    percentage_to_invoice = fields.Float(
        required=True,
    )
    rounding = fields.Float(
        string='Rounding Precision',
        required=True,
        help='Represent the non-zero value smallest coinage'
        ' (for example, 0.05).',
        default=0.01,
    )
    rounding_method = fields.Selection(
        required=True,
        selection=[('UP', 'UP'),
                   ('DOWN', 'DOWN'),
                   ('HALF-UP', 'HALF-UP')],
        default='HALF-UP',
        help='The tie-breaking rule used for float rounding operations',
    )

    @api.multi
    def compute_new_quantity(self):
        self.ensure_one()
        for line in self.invoice_id.invoice_line_ids:
            quantity = line.quantity * (self.percentage_to_invoice/100)
            line.quantity = float_round(
                quantity, precision_rounding=self.rounding,
                rounding_method=self.rounding_method)
        self.invoice_id.compute_taxes()
