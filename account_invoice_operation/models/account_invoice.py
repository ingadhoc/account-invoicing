# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.tools import float_round
from openerp.exceptions import ValidationError
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

    # Alternativa 2 (ver sale invoice line op/account_invoice_operation.py)
    # we call only on write on not with constrains because when we create an
    # invoice from a sale order operation lines where overwritten
    # @api.multi
    # def write(self, vals):
    #     res = super(AccountInvoice, self).write(vals)
    #     if vals.get('operation_ids'):
    #         self.operation_ids._run_checks()
    #     return res

    # Alternativa 1 (ver sale invoice line op/account_invoice_operation.py)
    @api.one
    @api.constrains('operation_ids')
    def run_checks(self):
        """
        If whe change operations the we run checks of that operations
        """
        self.operation_ids._run_checks()

    # TODO en la v9 no se soporta más el onchange sobr los o2m
    # ver este issue https://github.com/odoo/odoo/issues/2693
    # probamos de todo pero no lo pudimos hacer andar
    @api.one
    # @api.onchange('plan_id')
    @api.constrains('plan_id')
    def change_plan(self):
        self.operation_ids = False
        if self.plan_id:
            self.operation_ids = self.plan_id.get_plan_vals()

    @api.onchange('partner_id')
    def change_partner_set_plan(self):
        company = self.company_id
        if self.partner_id:
            partner = self.partner_id.commercial_partner_id
            self.plan_id = partner.with_context(
                force_company=company.id).default_sale_invoice_plan_id.id

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
        invoice_type = self.type
        remaining_op = len(self.operation_ids)
        sale_installed = False
        purchase_orders = []
        # if sale installed we get linked sales orders to update invoice links
        if self.env['ir.model'].search(
                [('model', '=', 'sale.order')]):
            sale_installed = True
        # if purchase installed we also update links
        if self.env['ir.model'].search(
                [('model', '=', 'purchase.order')]):
            purchase_orders = self.env['purchase.order'].search(
                [('invoice_ids', 'in', [self.id])])

        # if manual operations, we split by_quantity by default
        # split_type = 'by_quantity'
        # if self.plan_id:
        split_type = self.plan_id.split_type or 'by_quantity'
        if split_type == 'by_price':
            splt_field = 'price_unit'
        else:
            splt_field = 'quantity'
        last_quantities = {
            line.id: getattr(
                line, splt_field) for line in self.invoice_line_ids}

        for operation in self.operation_ids:
            default = {
                'operation_ids': False,
                'plan_id': False,
                # no copiamos para poder hacer control de las cantidades
                'invoice_line_ids': False,
            }

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
                    raise ValidationError(_(
                        'No %s journal found on company %s') % (
                        self.journal_type, company.name))
                default['journal_id'] = journal.id

            if operation.change_date:
                if operation.date:
                    default['date_invoice'] = operation.date
                else:
                    # TODO tal vez podamos pasar alguna fecha a esta funcion si
                    # interesa
                    default['date_invoice'] = operation._get_date()

            if operation.reference:
                default['reference'] = "%s%s" % (
                    self.reference or '', operation.reference)

            # if journal then journal has change and we need to
            # upate, at least, account_id
            if journal:
                tmp_inv = self.new(self.copy_data(default)[0])
                tmp_inv._onchange_partner_id()
                default.update({
                    'account_id': tmp_inv.account_id.id,
                    # we dont want to change fiscal position, bank or pay term
                    # the are share across companies
                    # 'partner_bank_id': tmp_inv.partner_bank_id.id,
                    # 'payment_term_id': tmp_inv.payment_term_id.id,
                })
                fiscal_position = self.fiscal_position_id
                # we only update fiscal position if original is for a company
                if fiscal_position and fiscal_position.company_id:
                    default[
                        'fiscal_position_id'] = tmp_inv.fiscal_position_id.id

            new_invoice = self.copy(default)

            for line in self.invoice_line_ids:
                # quantities could be price or quantity depending on split_type
                # if last operation and total perc 100 then we adjust qtys
                if remaining_op == 1 and total_percentage == 100.0:
                    new_quantity = last_quantities.get(line.id)
                else:
                    line_percentage = line._get_operation_percentage(operation)

                    new_quantity = getattr(
                        line, splt_field) * line_percentage / 100.0
                    if operation.rounding:
                        new_quantity = float_round(
                            new_quantity,
                            precision_rounding=operation.rounding)
                    last_quantities[line.id] = (
                        last_quantities.get(
                            line.id, getattr(line, splt_field)) - new_quantity)

                line_defaults = {
                    'invoice_id': new_invoice.id,
                    splt_field: new_quantity,
                }

                # if company has change, then we need to update lines
                if company and company != self.company_id:
                    # with copy data we get vals of copy
                    # we create record in cache and we call onchange
                    tmp_line = line.with_context(
                        force_company=company.id).new(
                        line.copy_data(line_defaults)[0])
                    tmp_line._onchange_product_id()

                    account_id = tmp_line.account_id.id
                    # not acconunt usually for lines without product
                    if not account_id:
                        prop = self.env['ir.property'].with_context(
                            force_company=company.id).get(
                            'property_account_income_categ_id',
                            'product.category')
                        prop_id = prop and prop.id or False
                        account_id = self.fiscal_position_id.map_account(
                            prop_id)
                        if not account_id:
                            raise ValidationError(_(
                                'There is no income account defined as global '
                                'property.'))

                    line_defaults.update({
                        'account_id': account_id,
                        'invoice_line_tax_ids': [
                            (6, 0, tmp_line.invoice_line_tax_ids.ids)],
                    })

                if new_quantity:
                    new_line = line.copy(line_defaults)
                    # if sale_orders we update links
                    if sale_installed:
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

            # if no invoice lines then we unlink the invoice
            if not new_invoice.invoice_line_ids:
                new_invoice.unlink()
            else:
                # update amounts for new invoice
                new_invoice.compute_taxes()
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
            self.invoice_line_ids.unlink()
            self.unlink()
            # actualizar pickings
        else:
            for line in self.invoice_line_ids:
                line_quantity = last_quantities.get(line.id)
                # if remaining qty = 0 we delete line
                if not line_quantity or line_quantity == 0.0:
                    line.unlink()
                else:
                    line.quantity = last_quantities.get(line.id)

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
            result['domain'] = [('id', 'in', invoices.ids)]
        else:
            form_view = self.env.ref(form_view_ref)
            result['views'] = [(form_view.id, 'form')]
            result['res_id'] = invoices.id
        return result

    @api.multi
    def signal_workflow(self, signal):
        """
        If someone calls "invoice_open" and invoice has operations, we run
        operations instead. This helps in compatibility, for eg with
        sale_order_type_automation
        """
        if signal == 'invoice_open':
            for invoice in self:
                if invoice.operation_ids:
                    invoice.action_run_operations()
                    self -= invoice
        return super(AccountInvoice, self).signal_workflow(signal)
