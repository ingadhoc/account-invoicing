from openerp import models, api, fields


class account_invoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def _default_journal(self):
        res = super(account_invoice, self)._default_journal()
        user = self.env.user
        invoice_type = self._context.get('type', False)
        if (
                invoice_type in ['out_invoice', 'out_refund'] and
                user.default_sale_journal_id):
            res = user.default_sale_journal_id
        elif (
                invoice_type in ['in_invoice', 'in_refund'] and
                user.default_purchase_journal_id):
            res = user.default_purchase_journal_id
        return res

    journal_id = fields.Many2one(
        'account.journal',
        default=_default_journal)
