from odoo import _, api, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains("journal_id")
    def _check_journal(self):
        """Check that the journal and the allows to post in the move's company."""
        moves = self.filtered(lambda x: x.state == "posted" and x.journal_id.l10n_latam_use_documents)
        if moves:
            raise UserError(
                _("You cannot change the journal of a posted move (%s).") % ", ".join(moves.mapped("display_name"))
            )
