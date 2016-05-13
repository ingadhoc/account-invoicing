# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class AccountInvoiceOperation(models.Model):
    _inherit = 'account.invoice.plan.line'
    _name = 'account.invoice.operation'
    _rec_name = 'display_name'

    display_name = fields.Char(
        compute='get_display_name',
    )
    number = fields.Integer(
        compute='get_display_name',
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

    @api.one
    @api.constrains('invoice_id', 'journal_id', 'company_id')
    def check_currencies(self):
        other_currency = (
            self.journal_id.currency or self.company_id.currency_id)
        if other_currency and self.invoice_id.currency_id != other_currency:
            raise Warning(_(
                'You can not use a journal or company of different currency '
                'than invoice currency yet. Operation "%s"') % (
                    self.display_name))

    @api.one
    @api.constrains('invoice_id', 'percentage')
    def check_percetantage(self):
        invoices = self.search(
            [('invoice_id', '=', self.invoice_id.id)])
        if sum(invoices.mapped('percentage')) > 100.0:
            raise Warning(_(
                'Sum of percentage could not be greater than 100%'))

    @api.multi
    @api.depends('percentage', 'date', 'journal_id.name')
    def get_display_name(self):
        # TODO suponemos que estamos viendo operaciones de una misma facutra
        # habria que agrupar por facturas antes de enumerar
        number = 1
        for operation in self:
            operation.number = number
            display_name = "%s) " % number
            number += 1
            if operation.amount_type == 'percentage':
                display_name += "%s%%" % operation.percentage
            else:
                display_name += _("Balance")
            if operation.date:
                display_name += " - %s" % operation.date
            elif operation.days2 and operation.days:
                display_name += " - %s" % operation.date
            if operation.journal_id:
                display_name += _(" - Days: %s/%s" % (
                    operation.days, operation.days2))
            elif operation.company_id:
                display_name += " - %s" % operation.company_id.name
            operation.display_name = display_name
