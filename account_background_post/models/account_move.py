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
    def _cron_background_post_invoices(self, batch_size=20, ids=None):
        """Busca las facturas que estan marcadas por ser validadas en background y las valida.

        Ponemos un batch size para mejorar la performance ya que odoo econimiza muchas queries al tener
        un prefetch_ids de 20 en vez de 1. pero ademas, iteramos y no mandamos el action_post a todos los
        records juntos para no tener problemas frente a facturas con error y envio de emails o cosas similares.
        Argumentos:
            - batch_size: Cantidad maxima de facturas a validar en este llamado.
            - ids: Si se pasa una lista de ids desde el ir_cron, solo se procesan esos registros.
        """

        moves = self.browse(ids) if ids is not None else self._get_background_post_due_moves()

        max_retries = self._get_background_post_max_retries()
        for move in moves[:batch_size]:
            try:
                move.action_post()
                self.env.cr.commit()  # pragma pylint: disable=invalid-commit
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
                    try:
                        # the hook is overridable, don't let it abort the whole cron run
                        move._notify_background_post_error(exp)
                    except Exception:
                        # the notification may have left the cursor aborted, keep at least the state
                        self.env.cr.rollback()
                        move._unschedule_background_post()
                        _logger.exception("Could not notify the background post error of invoice %s", move.id)
                    _logger.error("Error while trying to post invoice %s in background: %s", move.name or move.id, exp)
                # Commiteamos tras cada fallo para conservar el estado del reintento y el mensaje
                self.env.cr.commit()  # pragma pylint: disable=invalid-commit
        if len(moves) > batch_size:
            cron_id = self.env.context.get("cron_id")
            if cron_id:
                # Si tenemos cron_id en el contexto, usamos ese para relanzar la ejecucion.
                self.env["ir.cron"].browse(cron_id)._trigger()
                return
            self.env.ref("account_background_post.ir_cron_background_post_invoices")._trigger()

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

    def _get_background_post_error_body(self, error):
        return (
            _("We tried to validate this invoice on the background but got this error")
            + ": \n\n"
            + plaintext2html(str(error), "em")
        )

    def _notify_background_post_error(self, error):
        """Log the error on the invoice. Other modules may redirect it to the source document."""
        self.ensure_one()
        self.message_post(
            body=self._get_background_post_error_body(error),
            partner_ids=self.get_internal_partners().ids,
        )

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted.filtered("background_post")._unschedule_background_post()
        return posted
