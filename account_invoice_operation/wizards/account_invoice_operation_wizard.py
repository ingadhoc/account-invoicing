# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api


class account_invoice_operation_wizard(models.TransientModel):
    _name = 'account.invoice.operation.wizard'
    _description = 'Account Invoice Operation Wizard'

    @api.model
    def _get_invoice(self):
        return self._context.get('active_id', False)

    plan_id = fields.Many2one(
        'account.invoice.plan',
        'Plan',
        required=True,
        ondelete='cascade',
    )
    invoice_id = fields.Many2one(
        'account.invoice',
        'Invoice',
        default=_get_invoice,
        required=True,
        ondelete='cascade',
    )

    @api.onchange('invoice_id')
    def onchange_invoice(self):
        if self.invoice_id:
            self.plan_id = self.env['account.invoice.plan'].search(
                [('type', 'in', [self.invoice_id.journal_id.type, False])],
                limit=1)
            return {'domain': {'plan_id': [
                ('type', 'in', [self.invoice_id.journal_id.type, False])]}}
        else:
            self.plan_id = False

    @api.multi
    def confirm(self):
        self.ensure_one()
        active_id = self._context.get('active_id', False)
        active_model = self._context.get('active_id', False)
        if not active_id or not active_model:
            return True
        return self.plan_id.recreate_operations(
            self.invoice_id)
        # return self.invoice_id.action_invoice_operation()
