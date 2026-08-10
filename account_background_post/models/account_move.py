import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    background_post = fields.Boolean(
        help="If True then this invoice will be validated in the background by cron.", copy=False, tracking=True
    )
    background_post_date = fields.Datetime(
        string="Post in Background At",
        help="If set, the background cron waits until this date to post this invoice. If empty, the invoice is "
        "posted on the next cron run.",
        copy=False,
        tracking=True,
        index="btree_not_null",
    )
    background_post_attempts = fields.Integer(
        help="Number of failed attempts to post this invoice in the background.",
        copy=False,
        readonly=True,
    )

    @api.model
    def _get_background_post_max_retries(self):
        return int(self.env["ir.config_parameter"].sudo().get_param("account_background_post.max_retries", 0))

    @api.model
    def _get_background_post_retry_delay(self):
        return int(self.env["ir.config_parameter"].sudo().get_param("account_background_post.retry_delay_minutes", 30))

    def get_internal_partners(self):
        res = self.env["res.partner"]
        for partner in self.message_partner_ids:
            if partner.user_ids and all(user._is_internal() for user in partner.user_ids):
                res |= partner
        return res

    @api.model
    def _get_background_post_due_moves(self):
        # Las inmediatas primero: una tanda que falla y se reprograma no le tiene que comer el
        # turno a las que están sanas.
        domain = [("background_post", "=", True), ("state", "=", "draft")]
        immediate = self.search(domain + [("background_post_date", "=", False)])
        scheduled = self.search(
            domain + [("background_post_date", "<=", fields.Datetime.now())],
            order="background_post_date asc",
        )
        return immediate + scheduled

    @api.model
    def _cron_background_post_invoices(self, ids=None):
        """Busca las facturas que estan marcadas por ser validadas en background y las valida."""
        moves = self.browse(ids) if ids is not None else self._get_background_post_due_moves()

        total_len = len(moves)
        max_retries = self._get_background_post_max_retries()
        remaining_time = self.env["ir.cron"]._commit_progress(remaining=total_len)
        for index, move in enumerate(moves):
            if remaining_time <= 0:
                # Cortamos dejando `remaining` en el progreso: con eso el cron se reprograma.
                _logger.info(
                    "Background post cron ran out of time, %s invoices left for the next run",
                    total_len - index,
                )
                break
            try:
                move.action_post()
                remaining_time = self.env["ir.cron"]._commit_progress(processed=1)
            except Exception as exp:
                self.env.cr.rollback()
                if move._reschedule_background_post():
                    _logger.warning(
                        "Error while trying to post invoice %s in background, retry %s of %s scheduled for %s: %s",
                        move.name or move.id,
                        move.background_post_attempts,
                        max_retries,
                        move.background_post_date,
                        exp,
                    )
                else:
                    move._unschedule_background_post()
                    move.message_post(
                        # plaintext2html devuelve Markup, así que el body ya es html sin pasar
                        # body_is_html, que en 19 avisa por warning y en runbot tiñe el build
                        body=_("We tried to validate this invoice on the background but got this error")
                        + ": \n\n"
                        + plaintext2html(str(exp), "em"),
                        partner_ids=move.get_internal_partners().ids,
                    )
                    _logger.error("Error while trying to post invoice %s in background: %s", move.name, exp)
                # Commit after each failure to keep the retry state and the message
                remaining_time = self.env["ir.cron"]._commit_progress()

    def _reschedule_background_post(self):
        """Devuelve True si la factura quedó reprogramada y False si agotó los reintentos."""
        self.ensure_one()
        if self.background_post_attempts >= self._get_background_post_max_retries():
            return False
        self.write(
            {
                "background_post_attempts": self.background_post_attempts + 1,
                "background_post_date": fields.Datetime.now()
                + timedelta(minutes=self._get_background_post_retry_delay()),
            }
        )
        return True

    def _schedule_background_post(self, post_at=False):
        self.write({"background_post": True, "background_post_date": post_at, "background_post_attempts": 0})

    def _unschedule_background_post(self):
        self.write({"background_post": False, "background_post_date": False, "background_post_attempts": 0})

    def _post(self, soft=True):
        """Difiere el posteo de documentos de venta (facturas y notas de crédito) a background,
        para no bloquear el flujo sincrónico por validaciones externas lentas (ej. ARCA).

        Si el contexto trae `force_background_post`, saltea el `super()._post()` para facturas
        de cliente y notas de crédito/débito de venta (`out_invoice`, `out_refund`); el resto
        de los moves postea normalmente. El contexto puede traer una fecha en lugar de `True`
        para diferir el posteo hasta ese momento."""
        to_defer = self.env["account.move"]
        force = self.env.context.get("force_background_post")
        if force:
            to_defer = self.filtered(lambda m: m.move_type in ("out_invoice", "out_refund"))
            to_defer._schedule_background_post(False if force is True else fields.Datetime.to_datetime(force))
        posted = super(AccountMove, self - to_defer)._post(soft=soft)
        posted.filtered("background_post")._unschedule_background_post()
        return posted

    def _get_moves_requiring_confirmation(self):
        """Override method to always open the confirmation wizard
        when trying to set a background_post invoice.
        """
        return self
