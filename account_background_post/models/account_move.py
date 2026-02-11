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
<<<<<<< 6fc288bb68d27f2de9944b073dffd9aa40cd9453
    def _cron_background_post_invoices(self, ids=None):
        """Busca las facturas que estan marcadas por ser validadas en background y las valida."""
        if ids is not None:
            moves = self.browse(ids)
        else:
            moves = self.search([("background_post", "=", True), ("state", "=", "draft")])
||||||| 50ce5c596c073f799083e7ec14580da8b9aa4ce9
    def _cron_background_post_invoices(self, batch_size=20):
        """Busca las facturas que estan marcadas por ser validadas en background y las valida.
=======
    def _cron_background_post_invoices(self, batch_size=20, ids=None):
        """Busca las facturas que estan marcadas por ser validadas en background y las valida.
>>>>>>> f7e00de8e8098e6108c23fa758a26a82dfe9839a

<<<<<<< 6fc288bb68d27f2de9944b073dffd9aa40cd9453
        total_len = len(moves)
        self.env["ir.cron"]._commit_progress(remaining=total_len)
        for move in moves:
||||||| 50ce5c596c073f799083e7ec14580da8b9aa4ce9
        Ponemos un batch size para mejorar la performance ya que odoo econimiza muchas queries al tener
        un prefetch_ids de 20 en vez de 1. pero ademas, iteramos y no mandamos el atcion_post a todos los
        records juntos para no tener problemas frente a facturas con error y envio de emails o cosas similares
        """
        moves = self.search([("background_post", "=", True), ("state", "=", "draft")])

        for move in moves[:batch_size]:
=======
        Ponemos un batch size para mejorar la performance ya que odoo econimiza muchas queries al tener
        un prefetch_ids de 20 en vez de 1. pero ademas, iteramos y no mandamos el action_post a todos los
        records juntos para no tener problemas frente a facturas con error y envio de emails o cosas similares.
        Argumentos:
            - batch_size: Cantidad maxima de facturas a validar en este llamado.
            - ids: Si se pasa una lista de ids desde el ir_cron, solo se procesan esos registros.
        """

        if ids is not None:
            moves = self.browse(ids)
        else:
            moves = self.search([("background_post", "=", True), ("state", "=", "draft")])

        for move in moves[:batch_size]:
>>>>>>> f7e00de8e8098e6108c23fa758a26a82dfe9839a
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
<<<<<<< 6fc288bb68d27f2de9944b073dffd9aa40cd9453
                _logger.error("Error while trying to post invoice %s in background: %s", move.name, exp)
                # Commit after each failure to set false background_post and post the message
                self.env.cr.commit()  # pylint: disable=invalid-commit
||||||| 50ce5c596c073f799083e7ec14580da8b9aa4ce9
        if len(moves) > batch_size:
            self.env.ref("account_background_post.ir_cron_background_post_invoices")._trigger()
=======
        if len(moves) > batch_size:
            cron_id = self.env.context.get("cron_id")
            if cron_id:
                # Si tenemos cron_id en el contexto, usamos ese para relanzar la ejecucion.
                self.env["ir.cron"].browse(self.env.context["cron_id"])._trigger()
                return
            self.env.ref("account_background_post.ir_cron_background_post_invoices")._trigger()
>>>>>>> f7e00de8e8098e6108c23fa758a26a82dfe9839a

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted.filtered("background_post").background_post = False
        return posted

    def _get_moves_requiring_confirmation(self):
        """Override method to always open the confirmation wizard
        when trying to set a background_post invoice.
        """
        return self
