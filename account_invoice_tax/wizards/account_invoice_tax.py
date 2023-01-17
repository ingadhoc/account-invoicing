# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _, Command

class AccountInvoiceTax(models.TransientModel):

    _name = 'account.invoice.tax'
    _description = 'Account Invoice Tax'

    move_id = fields.Many2one('account.move', required=True)
    type_operation = fields.Selection([('add', 'Add Tax'), ('remove', 'Remove Tax')])
    tax_id = fields.Many2one('account.tax', required=True)
    amount = fields.Float()

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get(
            'active_model') == 'account.move' else self.env['account.move']
        res['move_id'] = move_ids[0].id if move_ids else False
        res['type_operation'] = self.env.context.get('type_operation', 'add')
        return res

    @api.onchange('move_id')
    def onchange_move_id(self):
        taxes = self.env['account.tax'].search([]) if self.type_operation == 'add' else self.move_id.mapped(
            'invoice_line_ids.tax_ids')
        return {'domain': {'tax_id': [('id', 'in', taxes.ids), ('company_id', '=', self.move_id.company_id.id)]}}

    def _get_amount_updated_values(self):
        debit = credit = 0
        if self.move_id.move_type == "in_invoice":
            if self.amount > 0:
                debit = self.amount
            elif self.amount < 0:
                credit = -self.amount
        else:  # For refund
            if self.amount > 0:
                credit = self.amount
            elif self.amount < 0:
                debit = -self.amount

        # If multi currency enable
        move_currency = self.move_id.currency_id
        company_currency = self.move_id.company_currency_id
        if move_currency and move_currency != company_currency:
            return {'amount_currency': self.amount if debit else -self.amount,
                    'debit': move_currency._convert(
                        debit, company_currency, self.move_id.company_id, self.move_id.invoice_date),
                    'credit': move_currency._convert(
                        credit, company_currency, self.move_id.company_id, self.move_id.invoice_date)}

        return {'debit': debit, 'credit': credit, 'balance': self.amount}

    def add_tax_and_new(self):
        self.add_tax()
        return {'type': 'ir.actions.act_window',
                'name': _('Edit tax lines'),
                'res_model': self._name,
                'target': 'new',
                'view_mode': 'form',
                'context': self._context,
            }

    def add_tax(self):
        """ Add the given taxes to all the invoice line of the current invoice """

        move = self.move_id
        fixed_taxes_bu = {
            line: {
                'amount_currency': line.amount_currency,
                'debit': line.debit,
                'credit': line.credit,
            } for line in move.line_ids.filtered(lambda x: x.tax_repartition_line_id.tax_id.amount_type == 'fixed')}

        # al crear la linea de impuesto no queda balanceado porque no recalcula las lineas AP/AR
        # por eso pasamos check_move_validity
        container = {'records': move.with_context(check_move_validity=False)}
        with move._check_balanced(container):
            with move._sync_dynamic_lines(container):
                move.invoice_line_ids.write({'tax_ids': [Command.link(self.tax_id.id)]})

        # set amount in the new created tax line. En este momento si queda balanceado y se ajusta la linea AP/AR
        container = {'records': move}
        with move._check_balanced(container):
            with move._sync_dynamic_lines(container):
                # restauramos todos los valores de impuestos fixed que se habrian recomputado
                commands = []
                for tax_line in move.line_ids.filtered(
                        lambda x: x.tax_repartition_line_id.tax_id.amount_type == 'fixed' and x in fixed_taxes_bu):
                    # ahora estamos mandando todo el write de una con el commands pero por si falla algo y queremos
                    # volver a probar, antes usabamos esta linea
                    # tax_line.write(fixed_taxes_bu.get(tax_line))
                    commands.append(Command.update(tax_line.id, fixed_taxes_bu.get(tax_line)))
                move.write({'line_ids': commands})

                # seteamos valor al impuesto segun lo que puso en el wizard
                line_with_tax = move.line_ids.filtered(lambda x: x.tax_line_id == self.tax_id)
                line_with_tax.write(self._get_amount_updated_values())

    def remove_tax(self):
        """ Remove the given taxes to all the invoice line of the current invoice """
        move_id = self.move_id.with_context(check_move_validity=False)
        fixed_taxes_bu = {
            line: {
                'amount_currency': line.amount_currency,
                'debit': line.debit,
                'credit': line.credit,
            } for line in move_id.line_ids.filtered(lambda x: x.tax_repartition_line_id.tax_id.amount_type == 'fixed')}
        container = {'records': move_id, 'self': move_id}
        with move_id._check_balanced(container):
            with move_id._sync_dynamic_lines(container):
                move_id.invoice_line_ids.write({'tax_ids': [Command.unlink(self.tax_id.id)]})
        for tax_line in move_id.line_ids.filtered(
            lambda x: x.tax_repartition_line_id.tax_id.amount_type == 'fixed' and x in fixed_taxes_bu):
            tax_line.write(fixed_taxes_bu.get(tax_line))
