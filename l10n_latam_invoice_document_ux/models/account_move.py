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

    def _update_sequence_made_gap(self, invalidate_current=False):
        """Los comprobantes cuyo diario usa documentos toman su numeración del documento, no de una
        secuencia administrada por el diario, por lo que los "saltos de secuencia" son normales y no
        deben marcarlos en rojo (decoration-danger).

        En v18 el flag lo computaba `_compute_made_sequence_gap` y `l10n_latam_invoice_document`
        ya excluía estos comprobantes. En v19 el cálculo se movió a `_update_sequence_made_gap`,
        pero el guard de upstream quedó sobre los métodos deprecados (`_compute_made_sequence_gap`
        y `_set_next_made_sequence_gap`), que ya no se ejecutan, dejándolo sin efecto. Reaplicamos
        acá la exclusión (mismo criterio que v18: todo comprobante con `l10n_latam_use_documents`)
        hasta que Odoo lo corrija upstream.
        """
        use_documents_moves = self.filtered(lambda m: m.l10n_latam_use_documents)
        use_documents_moves.made_sequence_gap = False
        if other_moves := self - use_documents_moves:
            super(AccountMove, other_moves)._update_sequence_made_gap(invalidate_current=invalidate_current)
