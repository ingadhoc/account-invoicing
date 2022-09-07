##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    number_lines = fields.Char(compute='_compute_number_lines')

    def _compute_number_lines(self):
        self.number_lines = False
        if self and not isinstance(self[0].id, int):
            return
        for move in self:
            number_line_map = {}
            for number, line in enumerate(move.invoice_line_ids.sorted("sequence"), 1):
                number_line_map.update({line.id: number})

            move.number_lines = number_line_map
