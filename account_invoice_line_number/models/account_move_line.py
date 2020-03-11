##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    number = fields.Integer(string="Line Nº", compute='_compute_number')

    def _compute_number(self):
        """No es lo mas elegante pero funciona. Algunos comentarios:
        * para evitar computos de mas no dejamos el depends y no se computa con los onchange
        * para hacer eso nos fijamos si lo que viene en self son new ids o enteros.
        * asignamos self.number porque si no da error, aparentemente por algo del mapped y el order.order_line.number
        """
        self.number = False
        if self and not isinstance(self[0].id, int):
            return
        for move in self.mapped('move_id'):
            number = 1
            for line in move.invoice_line_ids.sorted("sequence"):
                line.number = number
                number += 1
