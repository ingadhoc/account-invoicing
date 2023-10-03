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
        leaf = [('id', 'in', taxes.ids), ('type_tax_use', '=', 'purchase') ,('company_id', '=', self.move_id.company_id.id)]
        if self.env.context.get('group_id'):
            leaf += [('tax_group_id', '=', self.env.context.get('group_id'))]
        return {'domain': {'tax_id': leaf}}

    @api.onchange('tax_id')
    def onchange_tax_id(self):
        tax_line = self.move_id.line_ids.filtered(lambda x: x.tax_line_id  and x.tax_line_id.id == self.tax_id.id)
        if tax_line:
            self.amount = abs(tax_line.amount_currency)

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
            return {'amount_currency': self.amount if debit else -self.amount}

        return {'debit': debit, 'credit': credit, 'balance': self.amount if debit else -self.amount}

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
            line.tax_line_id: {
                'amount_currency': line.amount_currency,
                'debit': line.debit,
                'credit': line.credit,
            } for line in move.line_ids.filtered(lambda x: x.tax_repartition_line_id.tax_id.amount_type == 'fixed')}
        # al crear la linea de impuesto no queda balanceado porque no recalcula las lineas AP/AR
        # por eso pasamos check_move_validity
        container = {'records': move}
        with move.with_context(check_move_validity=False)._check_balanced(container):
            with move._sync_dynamic_lines(container):
                move.invoice_line_ids.filtered(lambda x: x.display_type not in ['line_section', 'line_note', 'payment_term']).write({'tax_ids': [Command.link(self.tax_id.id)]})

        # set amount in the new created tax line. En este momento si queda balanceado y se ajusta la linea AP/AR
        container = {'records': move}
        with move._check_balanced(container):
            with move._sync_dynamic_lines(container):
                # restauramos todos los valores de impuestos fixed que se habrian recomputado
                #restaured = []
                for tax_line in move.line_ids.filtered(
                        lambda x: x.tax_repartition_line_id.tax_id in fixed_taxes_bu and x.tax_repartition_line_id.tax_id.amount_type == 'fixed'):
                    tax_line.write(fixed_taxes_bu.get(tax_line.tax_line_id))

                # seteamos valor al impuesto segun lo que puso en el wizard
                line_with_tax = move.line_ids.filtered(lambda x: x.tax_line_id == self.tax_id)
                line_with_tax.write(self._get_amount_updated_values())

    def remove_tax(self):
        """ Remove the given taxes to all the invoice line of the current invoice """
        move_id = self.move_id.with_context(check_move_validity=False)
        fixed_taxes_bu = {
            line.tax_line_id: {
                'amount_currency': line.amount_currency,
                'debit': line.debit,
                'credit': line.credit,
            } for line in move_id.line_ids.filtered(lambda x: x.tax_repartition_line_id.tax_id.amount_type == 'fixed')}
        container = {'records': move_id, 'self': move_id}
        with move_id._check_balanced(container):
            with move_id._sync_dynamic_lines(container):
                move_id.invoice_line_ids.write({'tax_ids': [Command.unlink(self.tax_id.id)]})
        for tax_line in move_id.line_ids.filtered(
            lambda x: x.tax_repartition_line_id.tax_id in fixed_taxes_bu and x.tax_repartition_line_id.tax_id.amount_type == 'fixed'):
            tax_line.write(fixed_taxes_bu.get(tax_line.tax_line_id))

