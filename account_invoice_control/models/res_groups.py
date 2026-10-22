from odoo import models


class ResGroups(models.Model):
    _inherit = "res.groups"

    def _get_light_group_xmlids(self):
        return (
            *super()._get_light_group_xmlids(),
            "account_invoice_control.group_restrict_edit_invoice",
        )
