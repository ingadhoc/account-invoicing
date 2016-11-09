from openerp import models, fields


class account_invoice(models.Model):

    _inherit = 'res.users'

    default_purchase_journal_id = fields.Many2one(
        'account.journal',
        'Default Purchase Journal',
        domain=[('type', '=', 'purchase')]
    )
    default_sale_journal_id = fields.Many2one(
        'account.journal',
        'Default Sale Journal',
        domain=[('type', '=', 'sale')]
    )
