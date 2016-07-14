from openerp import models, api


class account_invoice(models.Model):

    _inherit = 'account.invoice'

    # @api.multi
    # def onchange_partner_id(
    #         self, type, partner_id, date_invoice=False,
    #         payment_term=False, partner_bank_id=False, company_id=False):
    #     ret = super(account_invoice, self).onchange_partner_id(
    #         type=type, partner_id=partner_id, date_invoice=date_invoice,
    #         payment_term=payment_term, partner_bank_id=partner_bank_id,
    #         company_id=company_id)
    #     if 'value' not in ret:
    #         ret['value'] = {}
    #     if partner_id:
    #         partner = self.env['res.partner'].browse(partner_id)
    #         ret['value']['user_id'] = partner.user_id.id or self.env.uid
    #     else:
    #         ret['value']['user_id'] = self.env.uid
    #     return ret

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        ret = super(account_invoice, self).onchange_partner_id()
        if self.partner_id and self.partner_id.user_id:
            self.user_id = self.partner_id.user_id.id
        else:
            self.user_id = self.env.uid
        return ret
