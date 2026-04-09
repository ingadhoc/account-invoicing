##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
##############################################################################

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    lock_posted_moves = fields.Boolean(
        string="Lock Posted Entries",
        default=False,
        help="If enabled, posted entries cannot be reset to draft. "
        "This provides protection against accidental modifications while "
        "allowing administrators to temporarily disable the lock when needed.\n\n"
        "This field replaces the deprecated 'restrict_mode_hash_table' system.",
    )
