from openerp import models, api


class account_invoice(models.Model):

    _inherit = 'account.invoice'

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        ret = super(account_invoice, self)._onchange_partner_id()
        if self.partner_id and self.partner_id.user_id:
            self.user_id = self.partner_id.user_id.id
        else:
            self.user_id = self.env.uid
        return ret
