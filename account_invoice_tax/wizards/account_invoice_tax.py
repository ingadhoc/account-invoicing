# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _, Command

class AccountInvoiceTax(models.TransientModel):

    _name = 'account.invoice.tax'
    _description = 'Account Invoice Tax'

    move_id = fields.Many2one('account.move', required=True)
    company_id = fields.Many2one(related='move_id.company_id')
    tax_line_ids = fields.One2many('account.invoice.tax_line', 'invoice_tax_id')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get(
            'active_model') == 'account.move' else self.env['account.move']
        res['move_id'] = move_ids[0].id if move_ids else False
        lines = []
        for line in move_ids[0].line_ids.filtered(lambda x: x.tax_line_id):
            lines.append(Command.create({'tax_id': line.tax_line_id.id ,'amount': line.amount_currency, 'new_tax':False}))
        res['tax_line_ids'] = lines

        return res

    def action_update_tax(self):
        move = self.move_id
        fixed_taxes_bu = {
            line.tax_line_id: {
                'amount_currency': line.amount_currency,
                'debit': line.debit,
                'credit': line.credit,
            } for line in self.move_id.line_ids.filtered(lambda x: x.tax_repartition_line_id.tax_id.amount_type == 'fixed')}

        active_tax = self.tax_line_ids.mapped('tax_id')
        origin_tax = self.move_id.line_ids.filtered(lambda x: x.tax_line_id).mapped('tax_repartition_line_id.tax_id')
        to_remove_tax = origin_tax - active_tax
        to_add_tax = active_tax - origin_tax
        container = {'records':move, 'self':move}

        # change tax list
        with move.with_context(check_move_validity=False)._check_balanced(container):
            with move._sync_dynamic_lines(container):
                if to_remove_tax:
                    move.invoice_line_ids.filtered(lambda x: x.display_type == 'product').write({'tax_ids': [Command.unlink(tax_id.id) for tax_id in to_remove_tax]})
                if to_add_tax:
                    move.invoice_line_ids.filtered(lambda x: x.display_type == 'product').write({'tax_ids': [Command.link(tax_id.id) for tax_id in to_add_tax]})

        # set amount in the new created tax line. En este momento si queda balanceado y se ajusta la linea AP/AR
        container = {'records': move}
        with move._check_balanced(container):
            with move._sync_dynamic_lines(container):
                # restauramos todos los valores de impuestos fixed que se habrian recomputado
                #restaured = []
                for tax_line in move.line_ids.filtered(
                        lambda x: x.tax_repartition_line_id.tax_id in fixed_taxes_bu and x.tax_repartition_line_id.tax_id.amount_type == 'fixed'):
                    tax_line.write(fixed_taxes_bu.get(tax_line.tax_line_id))
                for tax_line_id in self.tax_line_ids:
                    # seteamos valor al impuesto segun lo que puso en el wizard
                    line_with_tax = move.line_ids.filtered(lambda x: x.tax_line_id == tax_line_id.tax_id)
                    line_with_tax.write(tax_line_id._get_amount_updated_values())


    def add_tax_and_new(self):
        self.add_tax()
        return {'type': 'ir.actions.act_window',
                'name': _('Edit tax lines'),
                'res_model': self._name,
                'target': 'new',
                'view_mode': 'form',
                'context': self._context,
            }


class AccountInvoiceTax(models.TransientModel):

    _name = 'account.invoice.tax_line'
    _description = 'Account Invoice Tax line'

    invoice_tax_id = fields.Many2one('account.invoice.tax')
    tax_id = fields.Many2one('account.tax', required=True)
    amount = fields.Float()
    new_tax = fields.Boolean(default=True)

    def _get_amount_updated_values(self):
        debit = credit = 0
        if self.invoice_tax_id.move_id.move_type == "in_invoice":
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
        move_currency = self.invoice_tax_id.move_id.currency_id
        company_currency = self.invoice_tax_id.move_id.company_currency_id
        if move_currency and move_currency != company_currency:
            return {'amount_currency': self.amount if debit else -self.amount}

        return {'debit': debit, 'credit': credit, 'balance': self.amount if debit else -self.amount}
