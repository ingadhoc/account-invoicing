from openerp import models, api, fields


class account_invoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def _default_journal(self):
        res = super(account_invoice, self)._default_journal()
        user = self.env['res.users'].browse(self._uid)
        if self._context.get('type', False) == 'out_invoice' and user.default_sale_journal_id:
            res = user.default_sale_journal_id

        if self._context.get('type', False) == 'in_invoice' and user.default_purchase_journal_id:
            res = user.default_purchase_journal_id
        return res

    journal_id = fields.Many2one(
        'account.journal',
        default=_default_journal)

    @api.multi
    def onchange_company_id(self, company_id, part_id, type, invoice_line, currency_id):
        res = super(account_invoice, self).onchange_company_id(
            company_id, part_id, type, invoice_line, currency_id)
        default_journal = self._default_journal()
        if default_journal and default_journal.company_id.id == company_id:
            res['value']['journal_id'] = default_journal.id
        return res
