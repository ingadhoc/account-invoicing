from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ValidateAccountMove(models.TransientModel):

    _inherit = "validate.account.move"

    move_ids = fields.Many2many('account.move')
    count_inv = fields.Integer(help="Technical field to know the number of invoices selected from the wizard")
    batch_size = fields.Integer(compute='compute_batch_size')
    force_background = fields.Integer(compute='compute_force_background')

    def compute_batch_size(self):
        self.batch_size = self.env['ir.config_parameter'].sudo().get_param('account_background_post.batch_size', 20)

    def compute_force_background(self):
        for rec in self:
            rec.force_background = rec.count_inv > rec.batch_size

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        if self._context.get('active_model') == 'account.move':
            domain = [('id', 'in', self._context.get('active_ids', [])), ('state', '=', 'draft')]
        elif self._context.get('active_model') == 'account.journal':
            domain = [('journal_id', '=', self._context.get('active_id')), ('state', '=', 'draft')]
        else:
            raise UserError(_("Missing 'active_model' in context."))

        moves = self.env['account.move'].search(domain).filtered('line_ids')
        if not moves:
            raise UserError(_('There are no journal items in the draft state to post.'))

        res['move_ids'] = moves.ids
        res['count_inv'] = len(moves)
        return res

    def action_background_post(self):
        self.move_ids.background_post = True

    def validate_move(self):
        """ Sobre escribimos este metodo por completo para hacer:

        1. que se valida cada factura una a uno y no todas jutnas. esto para evitar problemas que puedan surgier
        por errores, que no se puedan ejecutar los commits que tenemos para guardar el estado de factura electronica y tambien para asegurar que tras cada fatura se envie su email, asi si hay un error posterior las facturas que fueron validadas aseguremos que hayan sido totalmente procesadas.

        2. Limitamos sui el usuario quiere validar mas facturas que el batch size definido directamente
        le pedimos que las valide en background. """

        if self.count_inv > self.batch_size:
            raise UserError(_('You can only validate on batches of size < %s invoices. If you need to validate'
                              ' more invoices please use the validate on background option', self.batch_size))

        for move in self.move_ids:
            _logger.info('Validating invoice %s', move.id)
            move._post(not self.force_post)
            move._cr.commit()

        return {'type': 'ir.actions.act_window_close'}
