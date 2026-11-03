##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import api, models


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    @api.ondelete(at_uninstall=False)
    def _unlink_archive_commission_rules(self):
        """Archive the commission rules of the deleted website categories.

        Once the category is gone the rule loses it and would apply to every product, so the
        rule is archived instead. Children categories are deleted in cascade by the database
        without going through the ORM, so their rules are archived here too. sudo: whoever
        deletes a website category does not need access to the commission rules.
        """
        self.env["account.commission.rule"].sudo().search([("public_category_id", "child_of", self.ids)]).active = False
