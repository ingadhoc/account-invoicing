# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, api, _
from openerp.exceptions import Warning


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        """
         We add currency rate on move creation so it can be used by electronic
        invoice later on action_number
        """
        if self.partner_id.commercial_partner_id.restrict_invoice:
            raise Warning(_('You can not validate an invoice'
                            ' for this partner "%s" while the field'
                            ' "restrict invoice" is set=True') % (
                self.partner_id.name))
        return super(account_invoice, self).action_move_create()
