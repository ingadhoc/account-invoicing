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
        rules = (
            self.env["account.commission.rule"]
            .sudo()
            .with_context(active_test=False)
            .search([("public_category_id", "child_of", self.ids)])
        )
        for rule in rules:
            rule.write({"active": False, "deleted_public_category": rule.public_category_id.display_name})
