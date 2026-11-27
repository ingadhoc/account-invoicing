# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    thermal_ticket_show_company = fields.Boolean(
        string="Show company data on thermal ticket",
        default=True,
        help="If unchecked, the thermal ticket omits the issuing company "
        "header (logo, name, address) and its contact details in the "
        "footer, printing only the invoice and customer data.",
    )
