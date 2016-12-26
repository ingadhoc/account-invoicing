# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
# import openerp.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import ValidationError


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
    type = fields.Selection([
        ('sale', 'Sale'),
        ('purchase', 'Purchase')],
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
    split_type = fields.Selection([
        ('by_quantity', 'By Quantity'),
        ('by_price', 'By Price (not recommended)')],
        default='by_quantity',
        required=True,
        help='By Price is not recommended because it could be not compatible '
        'with other modules and also because price analysis would not be ok'
    )

    @api.one
    @api.constrains('line_ids')
    def run_checks(self):
        self.line_ids._run_checks()

    @api.multi
    def get_plan_vals(self):
        self.ensure_one()
        operations_vals = []
        for line in self.line_ids:
            operations_vals.append((0, 0, line.get_operations_vals()))
        return operations_vals


class AccountInvoicePlanLine(models.Model):
    _name = 'account.invoice.plan.line'
    _order = 'sequence, id'

    sequence = fields.Integer(
        default=10,
        required=True,
    )
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
        # default=lambda self: self.env.user.company_id,
    )
    journal_id = fields.Many2one(
        'account.journal',
        'Journal',
        help='Journal can only be used if type is configured on plan',
    )
    # TODO add percentage
    amount_type = fields.Selection(
        [('percentage', 'Percentage'), ('balance', 'Balance')],
        'Amount Type',
        default='percentage',
        required=True,
    )
    percentage = fields.Float(
        'Percentage',
        # digits=dp.get_precision('Discount'),
        digits=(12, 6),
        required=False,
        help='Percentage of invoice lines quantities that will be used for '
        'this operation',
    )
    rounding = fields.Float(
        'Rounding Factor',
        digits=(12, 6),
        help='For eg, if you set 0.1, quani will be round to 1 decimal',
        # default=0.01,
    )
    change_date = fields.Boolean(
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
    @api.constrains('amount_type')
    @api.onchange('amount_type')
    def onchange_amount_type(self):
        if self.amount_type == 'balance':
            self.percentage = False
            self.rounding = False

    @api.one
    @api.onchange('company_id')
    def onchange_company(self):
        self.journal_id = False

    @api.multi
    def _run_checks(self):
        # this should be alled from grouping models like plan, invoice and
        # sale orders
        last_line = self.search(
            [('id', 'in', self.ids)], order='sequence desc, id desc', limit=1)
        balance_type_lines = self.search(
            [('id', 'in', self.ids), ('amount_type', '=', 'balance')])
        if len(balance_type_lines) > 1:
            raise ValidationError(_(
                'You can only configure one line with amount type balance'))
        elif balance_type_lines and balance_type_lines[0].id != last_line.id:
            raise ValidationError(_(
                'Line with amount type balance must be the last one'))
        percentage_lines = self.search([
            ('id', 'in', self.ids),
            ('amount_type', '=', 'percentage')])
        if sum(percentage_lines.mapped('percentage')) > 100.0:
            raise ValidationError(_(
                'Sum of lines percentage could not be greater than 100%'))

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
            'amount_type': self.amount_type,
            'rounding': self.rounding,
            'change_date': self.change_date,
            'days': self.days,
            'days2': self.days2,
            'reference': self.reference,
            'sequence': self.sequence,
        }
