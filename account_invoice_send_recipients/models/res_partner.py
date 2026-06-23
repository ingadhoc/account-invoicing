from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    send_invoice_by_email = fields.Boolean(
        string="Receive Invoices by Email",
        help="If enabled, this contact is automatically added as a recipient "
        "when sending invoices of the customer it belongs to.",
    )
