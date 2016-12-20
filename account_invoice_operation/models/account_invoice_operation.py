# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _


class AccountInvoiceOperation(models.Model):
    _inherit = 'account.invoice.plan.line'
    _name = 'account.invoice.operation'
    _rec_name = 'display_name'

    display_name = fields.Char(
        compute='get_display_name',
    )
    number = fields.Integer(
        compute='get_number',
    )
    # only required on plan line, not in operations
    plan_id = fields.Many2one(
        required=False,
        auto_join=True,
    )
    invoice_id = fields.Many2one(
        'account.invoice',
        'Invoice',
        ondelete='cascade',
        required=True,
        auto_join=True,
    )
    date = fields.Date(
        help='If you set a date here, then this date will be used and not '
        'computed.'
    )

    # we dont need this check because we keep original currency
    # @api.one
    # @api.constrains('invoice_id', 'journal_id', 'company_id')
    # def check_currencies(self):
    #     other_currency = (
    #         self.journal_id.currency or self.company_id.currency_id)
    #     if other_currency and self.invoice_id.currency_id != other_currency:
    #         raise ValidationError(_(
    #             'You can not use a journal or company of different currency '
    #             'than invoice currency yet. Operation "%s"') % (
    #                 self.display_name))

    @api.multi
    @api.depends('sequence', 'invoice_id')
    def get_number(self):
        for invoice in self.mapped('invoice_id'):
            number = 1
            operations = invoice.operation_ids.search([
                ('invoice_id', '=', invoice.id), ('id', 'in', self.ids)])
            for operation in operations:
                operation.number = number
                number += 1

    @api.multi
    @api.depends('percentage', 'date', 'journal_id.name', 'number')
    def get_display_name(self):
        for operation in self:
            display_name = "%s) " % operation.number
            if operation.amount_type == 'percentage':
                display_name += "%s%%" % operation.percentage
            else:
                display_name += _("Balance")
            if operation.change_date:
                if operation.date:
                    display_name += " - %s" % operation.date
                else:
                    display_name += _(" - Days: %s/%s") % (
                        operation.days, operation.days2)
            if operation.journal_id:
                display_name += " - %s" % operation.journal_id.name
            elif operation.company_id:
                display_name += " - %s" % operation.company_id.name
            operation.display_name = display_name
