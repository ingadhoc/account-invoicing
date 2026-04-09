##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
##############################################################################

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_draft(self):
        locked_moves = self.filtered(lambda m: m.journal_id.lock_posted_moves and m.state == "posted")

        if locked_moves:
            journal_names = ", ".join(locked_moves.mapped("journal_id.name"))
            raise UserError(
                _(
                    "Cannot reset to draft because the following journals have "
                    "'Lock Posted Entries' enabled: %s\n\n"
                    "To modify these entries, temporarily disable the lock on the journal, "
                    "make your changes, then re-enable the lock."
                )
                % journal_names
            )

        return super().button_draft()

    def _compute_show_reset_to_draft_button(self):
        super()._compute_show_reset_to_draft_button()

        for move in self:
            if move.journal_id.lock_posted_moves and move.state == "posted":
                move.show_reset_to_draft_button = False
