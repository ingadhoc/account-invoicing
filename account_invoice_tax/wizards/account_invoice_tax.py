# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import Command, api, fields, models
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

        active_tax = self.tax_line_ids.mapped("tax_id")
        origin_tax = self.move_id.line_ids.filtered(lambda x: x.tax_line_id).mapped("tax_repartition_line_id.tax_id")
        to_remove_tax = origin_tax - active_tax
        to_add_tax = active_tax - origin_tax
        container = {"records": move, "self": move}

        # --- 1. Update tax list on invoice lines ---
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

        # --- 2. Persist overrides in the JSON field so they survive recomputations ---
        self._save_overrides()

        # --- 3. Apply overrides to the current tax lines ---
        other_taxes_override = {}
        for wizard_line in self.tax_line_ids.filtered(lambda l: l.tax_id.amount_type != "fixed"):
            other_taxes_override[str(wizard_line.tax_id.id)] = {
                "amount": wizard_line.amount,
                "rate": self.move_id.invoice_currency_rate or 1.0,
            }
        container = {"records": move}
        with move._check_balanced(container):
            with move._sync_dynamic_lines(container):
                move._apply_tax_overrides(other_taxes_override=other_taxes_override)

    def _save_overrides(self):
        """Write wizard line amounts into ``tax_override_data`` on the move.

        Only fixed-amount taxes are persisted as overrides.  Percentage-based
        taxes are always recomputed automatically, so any stale entry for them
        is removed.
        """
        new_overrides = {}
        move = self.move_id
        for wizard_line in self.tax_line_ids.filtered(lambda l: l.tax_id.amount_type == "fixed"):
            new_overrides[str(wizard_line.tax_id.id)] = {
                "amount": wizard_line.amount,
                "rate": self.move_id.invoice_currency_rate or 1.0,
            }

        # Previous overrides are fully replaced – entries not present in
        # new_overrides (removed taxes or percentage-based taxes) are dropped.
        move.tax_override_data = new_overrides or False

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
