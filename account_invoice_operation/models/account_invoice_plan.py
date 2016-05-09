# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import Warning


class AccountInvoicePlan(models.Model):
    _name = 'account.invoice.plan'
    _order = 'sequence'

    name = fields.Char(
        'Name',
        required=True,
    )
    sequence = fields.Integer(
        default=10,
        required=True,
    )
    type = fields.Selection(
        [('sale', 'Sale'), ('purchase', 'Purchase')],
    )
    line_ids = fields.One2many(
        'account.invoice.plan.line',
        'plan_id',
        'Lines',
        copy=True,
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        help='This plan will be available only for this company or child ones,'
        ' if no company set then it will be available for all companies'
    )

    @api.multi
    def get_plan_vals(self):
        self.ensure_one()
        operations_vals = []
        for line in self.line_ids:
            operations_vals.append((0, 0, line.get_operations_vals()))
        return operations_vals

    @api.multi
    def recreate_operations(self, res_id, model):
        self.ensure_one()
        record = self.env[model].browse(res_id)
        record.operation_ids.unlink()
        if model == 'account.invoice':
            field = 'invoice_id'
            operations_model = 'account.invoice.operation'
        elif model == 'sale.order':
            field = 'order_id'
            operations_model = 'sale.invoice.operation'
        else:
            raise Warning(
                'Invoice operation with active_model %s not implemented '
                'yet' % self.model)

        for line in self.line_ids:
            operation_vals = line.get_operations_vals()
            operation_vals[field] = res_id
            operation_vals['plan_id'] = self.id
            self.env[operations_model].create(operation_vals)
        return True


class AccountInvoicePlanLine(models.Model):
    _name = 'account.invoice.plan.line'

    plan_id = fields.Many2one(
        'account.invoice.plan',
        'Plan',
        required=True,
        ondelete='cascade',
    )
    type = fields.Selection(
        related='plan_id.type',
        readonly=True,
    )
    reference = fields.Char(
        string='Invoice Reference',
        help="This reference will be added to invoice reference."
    )
    automatic_validation = fields.Boolean(
        help='After running operations, invoice are going to be validated',
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
    )
    journal_id = fields.Many2one(
        'account.journal',
        'Journal',
        help='Journal can only be used if type is configured on plan',
    )
    # TODO add percentage
    percentage = fields.Float(
        'Percentage',
        digits=dp.get_precision('Discount'),
        required=True,
        help='Percentage of invoice lines quantities that will be used for '
        'this operation',
    )
    rounding = fields.Float(
        'Rounding Factor',
        digits=(12, 6),
        help='For eg, if you set 0.1, quani will be round to 1 decimal',
        # default=0.01,
    )
    days = fields.Integer(
        'Number of Days',
        help="Number of days to add before computation of the day of month."
        "If Date=15/01, Number of Days=22, Day of Month=-1, then the due date "
        "is 28/02.",
    )
    days2 = fields.Integer(
        'Day of the Month',
        help="Day of the month, set -1 for the last day of the current month. "
        "If it's positive, it gives the day of the next month. Set 0 for net "
        "days (otherwise it's based on the beginning of the month)."
    )

    @api.one
    @api.onchange('company_id')
    def onchange_company(self):
        self.journal_id = False

    @api.one
    @api.constrains('plan_id', 'percentage')
    def check_percetantage(self):
        lines = self.search(
            [('plan_id', '=', self.plan_id.id)])
        if sum(lines.mapped('percentage')) > 100.0:
            raise Warning(_(
                'Sum of percentage could not be greater than 100%'))

    @api.multi
    def _get_date(self, date_ref=False):
        self.ensure_one()
        if not date_ref:
            date_ref = datetime.now().strftime('%Y-%m-%d')
        date = (datetime.strptime(
            date_ref, '%Y-%m-%d') + relativedelta(days=self.days))
        if self.days2 < 0:
            # Getting 1st of next month
            next_first_date = date + relativedelta(day=1, months=1)
            date = next_first_date + relativedelta(days=self.days2)
        if self.days2 > 0:
            date += relativedelta(day=self.days2, months=1)
        return date.strftime('%Y-%m-%d')

    @api.multi
    def get_operations_vals(self):
        self.ensure_one()
        return {
            'automatic_validation': self.automatic_validation,
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id,
            'percentage': self.percentage,
            'rounding': self.rounding,
            'days': self.days,
            'days2': self.days2,
            'reference': self.reference,
        }
