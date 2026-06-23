from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_invoice_extra_recipients(self):
        self.ensure_one()
        if self.move_type not in ("out_invoice", "out_refund"):
            return self.env["res.partner"]
        return self.env["res.partner"].search(
            [
                ("commercial_partner_id", "=", self.commercial_partner_id.id),
                ("send_invoice_by_email", "=", True),
                ("email", "!=", False),
            ]
        )
