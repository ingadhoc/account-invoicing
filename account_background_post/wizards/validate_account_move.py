import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ValidateAccountMove(models.TransientModel):
    _inherit = "validate.account.move"

    count_inv = fields.Integer(
        compute="_compute_count_inv", help="Technical field to know the number of invoices selected from the wizard"
    )
    batch_size = fields.Integer(compute="_compute_batch_size")
    force_background = fields.Integer(compute="_compute_force_background")

    @api.depends("move_ids")
    def _compute_count_inv(self):
        """It used to be set on default_get, which only sees the fields the ORM still has to
        default. Odoo 19 builds this wizard with create({'move_ids': ...}) from
        action_validate_moves_with_confirmation, so move_ids never reached default_get and the
        count stayed at 0, sending validate_move down the native _post() branch."""
        for rec in self:
            rec.count_inv = len(rec.move_ids)

    def _compute_batch_size(self):
        self.batch_size = self.env["account.move"]._get_background_post_batch_size()

    @api.depends("count_inv", "batch_size")
    def _compute_force_background(self):
        for rec in self:
            rec.force_background = rec.count_inv > rec.batch_size

    def action_background_post(self):
        self.move_ids.filtered(lambda m: m.state == "draft")._schedule_background_post()
        self.env.ref("account_background_post.ir_cron_background_post_invoices")._trigger()

    def validate_move(self):
        """Sobre escribimos este método para el caso de varias invoices para hacer:

        1. Que en lugar de hacer un _post hacemos un _action_post. esto porque odoo hace cosas como lanzar acciones y correr validaciones solo cuando corremos el action_post. y nosotros queremos que esas se apliquen. eso incluye el envio de email cuando validamos la factura.

        2. que se valida cada factura una a uno y no todas jutnas. esto para evitar problemas que puedan surgier
        por errores, que no se puedan ejecutar los commits que tenemos para guardar el estado de factura electronica y tambien para asegurar que tras cada fatura se envie su email, asi si hay un error posterior las facturas que fueron validadas aseguremos que hayan sido totalmente procesadas.

        3. Limitamos sui el usuario quiere validar mas facturas que el batch size definido directamente
        le pedimos que las valide en background."""
        if self.count_inv:
            if self.count_inv > self.batch_size:
                raise UserError(
                    _(
                        "You can only validate on batches of size < %s invoices. If you need to validate"
                        " more invoices please use the validate on background option",
                        self.batch_size,
                    )
                )

            for move in self.move_ids:
                _logger.info("Validating invoice %s", move.id)
                move.action_post()
                move.env.cr.commit()

            return {"type": "ir.actions.act_window_close"}
        else:
            return super().validate_move()

    def validate_move_confirm(self):
        """Bridge method called from the view's Confirm button renamed to
        avoid name collision. It delegates to `validate_move` to keep the
        same behaviour."""
        return self.validate_move()
