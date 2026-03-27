import logging

from odoo import _, api, fields, models
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    background_post = fields.Boolean(
        help="If True then this invoice will be validated in the background by cron.", copy=False, tracking=True
    )

    def get_internal_partners(self):
        res = self.env["res.partner"]
        for partner in self.message_partner_ids:
            if partner.user_ids and all(user._is_internal() for user in partner.user_ids):
                res |= partner
        return res

    @api.model
    def _cron_background_post_invoices(self, ids=None):
        """Busca las facturas que estan marcadas por ser validadas en background y las valida."""
        if ids is not None:
            moves = self.browse(ids)
        else:
            moves = self.search([("background_post", "=", True), ("state", "=", "draft")])

        total_len = len(moves)
        self.env["ir.cron"]._commit_progress(remaining=total_len)
        for move in moves:
            try:
                move.action_post()
                self.env["ir.cron"]._commit_progress(processed=1)
            except Exception as exp:
                self.env.cr.rollback()
                move.background_post = False
                move.message_post(
                    body=_("We tried to validate this invoice on the background but got this error")
                    + ": \n\n"
                    + plaintext2html(str(exp), "em"),
                    partner_ids=move.get_internal_partners().ids,
                    body_is_html=True,
                )
<<<<<<< 24dad28271a7be0f910c94eae5e492a680c86b6a
                _logger.error("Error while trying to post invoice %s in background: %s", move.name, exp)
                # Commit after each failure to set false background_post and post the message
                self.env.cr.commit()  # pylint: disable=invalid-commit
||||||| e2e735e96b98dcfb95dc414b45e83a0e358e6ebc
        if len(moves) > batch_size:
            cron_id = self.env.context.get("cron_id")
            if cron_id:
                # Si tenemos cron_id en el contexto, usamos ese para relanzar la ejecucion.
                self.env["ir.cron"].browse(self.env.context["cron_id"])._trigger()
                return
            self.env.ref("account_background_post.ir_cron_background_post_invoices")._trigger()
=======
                self.env.cr.commit()  # pragma pylint: disable=invalid-commit
        if len(moves) > batch_size:
            cron_id = self.env.context.get("cron_id")
            if cron_id:
                # Si tenemos cron_id en el contexto, usamos ese para relanzar la ejecucion.
                self.env["ir.cron"].browse(self.env.context["cron_id"])._trigger()
                return
            self.env.ref("account_background_post.ir_cron_background_post_invoices")._trigger()
>>>>>>> 845cecc44510119365244ebbd27b9d8ce1146047

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted.filtered("background_post").background_post = False
        return posted

    def _get_moves_requiring_confirmation(self):
        """Override method to always open the confirmation wizard
        when trying to set a background_post invoice.
        """
        return self
