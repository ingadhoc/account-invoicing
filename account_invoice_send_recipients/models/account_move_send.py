from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _get_default_mail_partner_ids(self, move, mail_template, mail_lang):
        partners = super()._get_default_mail_partner_ids(move, mail_template, mail_lang)
        return partners | move._get_invoice_extra_recipients()
