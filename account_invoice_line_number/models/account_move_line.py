##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    number = fields.Integer(string="Line Nº", compute="_compute_number")

    def _compute_number(self):
        """No es lo mas elegante pero funciona. Algunos comentarios:
        * para evitar computos de mas no dejamos el depends y no se computa con los onchange
        * para hacer eso nos fijamos si lo que viene en self son new ids o enteros.
        * asignamos self.number porque si no da error, aparentemente por algo del mapped y el order.order_line.number
        """
        self.number = False
        if self and not isinstance(self[0].id, int):
            return
        to_set = set(self.ids)
        for move in self.move_id:
            product_lines = move.line_ids.filtered(lambda l: l.display_type == "product").sorted("sequence")
            for number, line in enumerate(product_lines, 1):
                if line.id in to_set:
                    line.number = number
