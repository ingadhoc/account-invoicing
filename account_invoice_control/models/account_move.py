##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    restrict_edit_invoice = fields.Boolean(compute="_compute_restrict_edit_invoice")
    has_sales = fields.Boolean(string="Has Sales?", compute="_compute_has_sales")

    def _compute_restrict_edit_invoice(self):
        if self.env.user.has_group("account_invoice_control.group_restrict_edit_invoice"):
            self.restrict_edit_invoice = True
        else:
            self.restrict_edit_invoice = False

    def _compute_has_sales(self):
        moves = self.filtered(lambda move: move.is_sale_document())
        (self - moves).has_sales = False
        for rec in moves:
            rec.has_sales = any(line for line in rec.invoice_line_ids.mapped("sale_line_ids"))
