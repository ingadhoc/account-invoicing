# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceTax(models.TransientModel):
    _name = "account.invoice.tax"
    _description = "Account Invoice Tax"

    move_id = fields.Many2one("account.move", required=True)
    tax_line_ids = fields.One2many("account.invoice.tax_line", "invoice_tax_id")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        move_ids = (
            self.env["account.move"].browse(self.env.context["active_ids"])
            if self.env.context.get("active_model") == "account.move"
            else self.env["account.move"]
        )
        res["move_id"] = move_ids[0].id if move_ids else False
        if move_ids[0].move_type == "in_invoice":
            sign = 1
        else:  # For refund
            sign = -1
        lines = []
        for line in move_ids[0].line_ids.filtered(lambda x: x.tax_line_id):
            lines.append(
                Command.create({"tax_id": line.tax_line_id.id, "amount": line.amount_currency * sign, "new_tax": False})
            )
        res["tax_line_ids"] = lines

        return res

    def action_update_tax(self):
        move = self.move_id
        fixed_taxes_bu = {
            line.tax_line_id: {
                "amount_currency": line.amount_currency,
                "debit": line.debit,
                "credit": line.credit,
            }
            for line in self.move_id.line_ids.filtered(
                lambda x: x.tax_repartition_line_id.tax_id.amount_type == "fixed"
            )
        }

        active_tax = self.tax_line_ids.mapped("tax_id")
        origin_tax = self.move_id.line_ids.filtered(lambda x: x.tax_line_id).mapped("tax_repartition_line_id.tax_id")
        to_remove_tax = origin_tax - active_tax
        to_add_tax = active_tax - origin_tax
        container = {"records": move, "self": move}

        # change tax list
        with move.with_context(check_move_validity=False)._check_balanced(container):
            with move._sync_dynamic_lines(container):
                if to_remove_tax:
                    move.invoice_line_ids.filtered(lambda x: x.display_type == "product").write(
                        {"tax_ids": [Command.unlink(tax_id.id) for tax_id in to_remove_tax]}
                    )
                if to_add_tax:
                    move.invoice_line_ids.filtered(lambda x: x.display_type == "product").write(
                        {"tax_ids": [Command.link(tax_id.id) for tax_id in to_add_tax]}
                    )

        # set amount in the new created tax line. En este momento si queda balanceado y se ajusta la linea AP/AR
        container = {"records": move}

        if move.move_type == "in_invoice":
            sign = 1
        else:  # For refund
            sign = -1
        with move._check_balanced(container):
            with move._sync_dynamic_lines(container):
                # restauramos todos los valores de impuestos fixed que se habrian recomputado
                # restaured = []
                for tax_line in move.line_ids.filtered(
                    lambda x: x.tax_repartition_line_id.tax_id in fixed_taxes_bu
                    and x.tax_repartition_line_id.tax_id.amount_type == "fixed"
                ):
                    tax_line.write(fixed_taxes_bu.get(tax_line.tax_line_id))
                for tax_line_id in self.tax_line_ids:
                    # seteamos valor al impuesto segun lo que puso en el wizard
                    line_with_tax = move.line_ids.filtered(lambda x: x.tax_line_id == tax_line_id.tax_id)
                    line_with_tax.write({"amount_currency": tax_line_id.amount * sign})

    def add_tax_and_new(self):
        self.add_tax()
        return {
            "type": "ir.actions.act_window",
            "name": _("Edit tax lines"),
            "res_model": self._name,
            "target": "new",
            "view_mode": "form",
            "context": self._context,
        }

    @api.constrains("tax_line_ids")
    @api.onchange("tax_line_ids")
    def check_analytic(self):
        taxes = self.tax_line_ids.filtered("tax_id.analytic").mapped("tax_id")
        if taxes:
            raise UserError(
                'No puede usar este asistente ya que algún impuesto tiene establecido "Incluir en el costo analítico?".\nImpuestos: %s'
                % (", ".join(taxes.mapped(lambda x: "%s (%s)" % (x.name, x.id))))
            )


class AccountInvoiceTaxLine(models.TransientModel):
    _name = "account.invoice.tax_line"
    _description = "Account Invoice Tax line"
    _check_company_auto = True
    _check_company_domain = models.check_companies_domain_parent_of

    invoice_tax_id = fields.Many2one("account.invoice.tax")
    tax_id = fields.Many2one(
        "account.tax",
        required=True,
        check_company=True,
        domain="[('type_tax_use', '=', 'purchase'), ('id', 'not in', existing_tax_ids)]",
    )
    company_id = fields.Many2one(related="invoice_tax_id.move_id.company_id")
    currency_id = fields.Many2one(related="invoice_tax_id.move_id.currency_id")
    existing_tax_ids = fields.Many2many("account.tax", compute="_compute_existing_taxes")
    amount = fields.Monetary(
        currency_field="currency_id",
    )
    new_tax = fields.Boolean(default=True)

    @api.depends("invoice_tax_id.tax_line_ids.tax_id")
    def _compute_existing_taxes(self):
        for record in self:
            record.existing_tax_ids = record.invoice_tax_id.tax_line_ids.mapped("tax_id")
