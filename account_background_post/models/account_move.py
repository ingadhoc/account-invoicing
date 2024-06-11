from odoo import _, api, fields, models
from odoo.tools import plaintext2html


class AccountMove(models.Model):

    _inherit = 'account.move'

    background_post = fields.Boolean(help="If True then this invoice will be validated in the background by cron.", copy=False, tracking=True)

    def get_internal_partners(self):
        res = self.env['res.partner']
        for partner in self.message_partner_ids:
            if partner.user_ids and all(user._is_internal() for user in partner.user_ids):
                res |= partner
        return res

    @api.model
    def _cron_background_post_invoices(self, batch_size=20):
        """ Busca las facturas que estan marcadas por ser validadas en background y las valida.

        Ponemos un batch size para mejorar la performance ya que odoo econimiza muchas queries al tener
        un prefetch_ids de 20 en vez de 1. pero ademas, iteramos y no mandamos el atcion_post a todos los
        records juntos para no tener problemas frente a facturas con error y envio de emails o cosas similares
        """
        moves = self.search([('background_post', '=', True), ('state', '=', 'draft')])

        for move in moves[:batch_size]:
            try:
                move.action_post()
                move._cr.commit()
            except Exception as exp:
                self.env.cr.rollback()
                move.background_post = False
                move.message_post(
                    body=_('We tried to validate this invoice on the background but got this error') + ': \n\n' + plaintext2html(str(exp), 'em'),
                    partner_ids=move.get_internal_partners().ids,
                    body_is_html=True)
        if len(moves) > batch_size:
            self.env.ref('account_background_post.ir_cron_background_post_invoices')._trigger()

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted.filtered('background_post').background_post = False
        return posted
