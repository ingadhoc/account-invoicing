# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.tools import float_round
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def _get_operation_percentage(self, operation):
        """For compatibility with sale invoice operation line"""
        self.ensure_one()
        if operation.amount_type == 'percentage':
            return operation.percentage
        else:
            return 100.0 - sum(operation.invoice_id.operation_ids.mapped(
                'percentage'))


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    operation_ids = fields.One2many(
        'account.invoice.operation',
        'invoice_id',
        'Operations',
        readonly=True,
        copy=True,
        states={'draft': [('readonly', False)]}
    )
    journal_type = fields.Selection(
        related='journal_id.type',
        readonly=True,
    )
    plan_id = fields.Many2one(
        'account.invoice.plan',
        'Plan',
        # required=True,
        # ondelete='cascade',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    # we leave this field so it can be understand what can happen, for ex in
    # lines
    readonly_operation_ids = fields.One2many(
        related='operation_ids',
        readonly=True,
    )
    readonly_plan_id = fields.Many2one(
        related='plan_id',
        readonly=True,
    )

    @api.one
    @api.constrains('operation_ids')
    def run_checks(self):
        self.operation_ids._run_checks()

    @api.one
    @api.onchange('plan_id')
    def change_plan(self):
        self.operation_ids = False
        if self.plan_id:
            self.operation_ids = self.plan_id.get_plan_vals()

    @api.multi
    def onchange_partner_id(
            self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        result = super(AccountInvoice, self).onchange_partner_id(
            type, partner_id, date_invoice=date_invoice,
            payment_term=payment_term, partner_bank_id=partner_bank_id,
            company_id=company_id)
        if partner_id:
            partner = self.env['res.partner'].with_context(
                force_company=company_id).browse(
                partner_id).commercial_partner_id
            result['value'][
                'plan_id'] = partner.default_sale_invoice_plan_id.id
        return result

    @api.multi
    def action_run_operations(self):
        self.ensure_one()
        invoices = self
        # TODO tal vez podemos agregar un campo calculado y hacer que devuevla
        # el porcentaje segun si es balance o porcentaje, el tema es que
        # el agrupador varia de modelo a modelo
        # if there is a line with balance we have 100.0, else we have
        total_percentage = self.operation_ids.filtered(
            lambda x: x.amount_type == 'balance') and 100.0 or sum(
            self.operation_ids.mapped('percentage'))
        last_quantities = {
            line.id: line.quantity for line in self.invoice_line}
        invoice_type = self.type
        remaining_op = len(self.operation_ids)
        sale_orders = []
        purchase_orders = []
        # if sale installed we get linked sales orders to update invoice links
        if self.env['ir.model'].search(
                [('model', '=', 'sale.order')]):
            sale_orders = self.env['sale.order'].search(
                [('invoice_ids', 'in', [self.id])])
        # if purchase installed we also update links
        if self.env['ir.model'].search(
                [('model', '=', 'purchase.order')]):
            purchase_orders = self.env['purchase.order'].search(
                [('invoice_ids', 'in', [self.id])])

        for operation in self.operation_ids:
            default = {
                'operation_ids': False,
                # no copiamos para poder hacer control de las cantidades
                'invoice_line': False,
                # do not copy period (if we want it we should get right period
                # for the date, eg. in inter_company_rules)
                'period_id': False,
            }

            # por compatibilidad con stock_picking_invoice_link
            # como el campo nuevo tiene copy=False lo copiamos nosotros
            if 'picking_ids' in self._fields:
                default['picking_ids'] = [(6, 0, self.sudo().picking_ids.ids)]

            company = False
            journal = False
            # if op journal and is different from invoice journal
            if (
                    operation.journal_id and
                    operation.journal_id != self.journal_id):
                company = operation.journal_id.company_id
                journal = operation.journal_id
                default['journal_id'] = journal.id
                default['company_id'] = company.id
            # if op company and is different from invoice company
            elif (
                    operation.company_id and
                    operation.company_id != self.company_id):
                company = operation.company_id
                default['company_id'] = operation.company_id.id
                # we get a journal in new company
                journal = self.with_context(
                    company_id=company.id)._default_journal()
                if not journal:
                    raise Warning(_('No %s journal found on company %s') % (
                        self.journal_type, company.name))
                default['journal_id'] = journal.id

            if operation.date:
                default['date_invoice'] = operation.date
            elif operation.days and operation.days2:
                # TODO tal vez podamos pasar alguna fecha a esta funcion si
                # interesa
                default['date_invoice'] = operation._get_date()

            # if journal then journal has change and we need to
            # upate, at least, account_id
            if journal:
                partner_data = self.onchange_partner_id(
                    invoice_type, self.partner_id.id,
                    date_invoice=default.get(
                        'date_invoice', False) or self.date_invoice,
                    payment_term=self.payment_term.id,
                    company_id=company.id)['value']
                default.update({
                    'account_id': partner_data.get('account_id', False),
                    # we dont want to change fiscal position
                    # 'fiscal_position': partner_data.get(
                    #     'fiscal_position', False),
                    'partner_bank_id': partner_data.get(
                        'partner_bank_id', False),
                    'payment_term': partner_data.get('payment_term', False),
                })

            if operation.reference:
                default['reference'] = "%s%s" % (
                    self.reference or '', operation.reference)

            new_invoice = self.copy(default)

            for line in self.invoice_line:
                # if last operation and total perc 100 then we adjust qtys
                if remaining_op == 1 and total_percentage == 100.0:
                    new_quantity = last_quantities.get(line.id)
                else:
                    line_percentage = line._get_operation_percentage(operation)
                    new_quantity = line.quantity * line_percentage / 100.0
                    if operation.rounding:
                        new_quantity = float_round(
                            new_quantity,
                            precision_rounding=operation.rounding)
                    last_quantities[line.id] = (
                        last_quantities.get(
                            line.id, line.quantity) - new_quantity)

                line_defaults = {
                    'invoice_id': new_invoice.id,
                    'quantity': new_quantity,
                }
                # por compatibilidad con stock_picking_invoice_link
                # como el campo nuevo tiene copy=False lo copiamos nosotros
                if 'move_line_ids' in self._fields:
                    default['move_line_ids'] = [
                        (6, 0, line.sudo().move_line_ids.ids)]

                # if company has change, then we need to update lines
                if company and company != self.company_id:
                    line_data = line.with_context(
                        force_company=company.id).sudo().product_id_change(
                            line.product_id.id,
                            line.product_id.uom_id.id,
                            qty=new_quantity,
                            name='',
                            type=invoice_type,
                            partner_id=self.partner_id.id,
                            fposition_id=self.fiscal_position.id,
                            company_id=company.id)
                    # we only update account and taxes

                    account_id = line_data['value'].get('account_id')
                    # not acconunt usually for lines without product
                    if not account_id:
                        prop = self.env['ir.property'].with_context(
                            force_company=company.id).get(
                            'property_account_income_categ',
                            'product.category')
                        prop_id = prop and prop.id or False
                        account_id = self.fiscal_position.map_account(prop_id)
                        if not account_id:
                            raise Warning(_(
                                'There is no income account defined as global '
                                'property.'))

                    line_defaults.update({
                        'account_id': account_id,
                        'invoice_line_tax_id': [
                            (6, 0, line_data['value'].get(
                                'invoice_line_tax_id', []))],
                    })

                if new_quantity:
                    new_line = line.copy(line_defaults)
                    # if sale_orders we update links
                    if sale_orders:
                        sale_lines = self.env['sale.order.line'].search(
                            [('invoice_lines', 'in', [line.id])])
                        sale_lines.write({'invoice_lines': [(4, new_line.id)]})

                    if purchase_orders:
                        purchas_lines = self.env['purchase.order.line'].search(
                            [('invoice_lines', 'in', [line.id])])
                        purchas_lines.write(
                            {'invoice_lines': [(4, new_line.id)]})
                        purchase_orders.write(
                            {'invoice_ids': [(4, new_invoice.id)]})

            # not sure why but in some cases we need to update this and in
            # others it is updated automatically
            for order in sale_orders:
                if new_invoice not in order.invoice_ids:
                    self._cr.execute(
                        'insert into sale_order_invoice_rel (order_id, invoice_id) values (%s,%s)', (
                            order.id, new_invoice.id))

            # if no invoice lines then we unlink the invoice
            if not new_invoice.invoice_line:
                new_invoice.unlink()
            else:
                # update amounts for new invoice
                new_invoice.button_reset_taxes()
                if operation.automatic_validation:
                    new_invoice.signal_workflow('invoice_open')

                invoices += new_invoice

            # update remaining operations
            remaining_op -= 1

        # if operations sum 100, then we delete parent invoice, if not, then
        # we delete operations after succes operation
        self.operation_ids.unlink()
        # we delete original invoice if at least one was created and no need
        # for thisone
        if total_percentage == 100.0 and len(invoices) > 1:
            invoices -= self
            # we redirect workflow so that sale order doenst goes to except
            # state and also if we delete new invoice it sends to except
            # we only send first invoice because it does not works ok with many
            # invoices
            self.redirect_workflow([(self.id, invoices[0].id)])
            # borrar factura
            # por compatibilidad con sale commission, borramos las lineas y
            # luego la factura
            self.invoice_line.unlink()
            self.unlink()
            # actualizar pickings
        else:
            for line in self.invoice_line:
                line_quantity = last_quantities.get(line.id)
                # if remaining qty = 0 we delete line
                if not line_quantity or line_quantity == 0.0:
                    line.unlink()
                else:
                    line.quantity = last_quantities.get(line.id)
            # self.operation_ids.unlink()

        # por compatibilidad con stock_picking_invoice_link
        # we set all related pickings on invoiced state
        if 'picking_ids' in self._fields:
            pickings = invoices.sudo().mapped('picking_ids').filtered(
                lambda x: x.state != 'cancel')
            pickings.write({'invoice_state': 'invoiced'})

        # set plan false for all invoices
        invoices.write({'plan_id': False})

        if invoice_type in ['out_invoice', 'out_refund']:
            action_ref = 'account.action_invoice_tree1'
            form_view_ref = 'account.invoice_form'
        else:
            action_ref = 'account.action_invoice_tree2'
            form_view_ref = 'account.invoice_supplier_form'
        action = self.env.ref(action_ref)
        result = action.read()[0]

        if len(invoices) > 1:
            # result[
            result['domain'] = [('id', 'in', invoices.ids)]
        else:
            form_view = self.env.ref(form_view_ref)
            result['views'] = [(form_view.id, 'form')]
            result['res_id'] = invoices.id
        return result
