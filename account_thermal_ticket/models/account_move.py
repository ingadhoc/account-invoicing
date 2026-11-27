# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_print_thermal_receipt(self):
        """Trigger the thermal receipt print with auto-print dialog.

        Returns a client action handled by the ``thermal_print`` JS handler,
        which opens the report in a standalone window to avoid CSS conflicts
        with the backend DOM.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "thermal_print",
            "context": {
                "report_name": self._get_thermal_receipt_report_name(),
                "invoice_id": self.id,
            },
        }

    def _get_thermal_receipt_report_name(self):
        """Return the QWeb report to render for this invoice.

        Single extension point of the module: localization modules override
        this to return their own report when the invoice qualifies, falling
        back to ``super()`` otherwise. That way the user always sees one
        "Imprimir Ticket Térmico" button and the right template is picked
        based on the invoice itself.
        """
        self.ensure_one()
        return "account_thermal_ticket.report_thermal_invoice_html"

    def get_current_time_formatted(self):
        """Return the current time in the user's timezone as HH:MM."""
        self.ensure_one()
        current_time_local = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return current_time_local.strftime("%H:%M")

    def _get_thermal_header_partner(self):
        """Return the partner whose data heads the receipt.

        Single source of the issuer block (logo, name and address), so every
        template that renders a thermal ticket prints the same issuer.
        Localization modules override this when the issuing address does not
        come from the company, e.g. the partner of an ARCA point of sale.
        """
        self.ensure_one()
        return self.company_id.partner_id

    def _get_thermal_header_logo(self):
        """Return the image that heads the receipt, or False for none.

        Walks from the most specific issuer to the most general: the contact
        of the point of sale, then the company issuing the document, then the
        company at the root of the group. A branch opened for internal
        documents has no brand of its own, and the group logo heads its
        ticket better than a blank does.

        A company nobody gave a logo to does not have an empty field: it
        carries Odoo's "Your logo" placeholder, because `res.company.logo`
        is related to the partner image and born with a default. On an 80mm
        ticket that placeholder takes the whole top of the paper and says
        nothing, so a company wearing it is skipped like one with no logo.
        For a company of the chain the flag the native templates test,
        `uses_default_logo`, answers it; for the contact of the point of
        sale -which may well be the partner of another company- the image
        is compared against the placeholder itself.
        """
        self.ensure_one()
        partner = self._get_thermal_header_partner()
        company_partner = self.company_id.partner_id
        if partner != company_partner and partner.image_1920:
            default_logo = self.env["res.company"]._get_logo()
            if partner.image_1920 != default_logo:
                return partner.image_1920
        for company in (self.company_id, self.company_id.root_id):
            if not company.uses_default_logo:
                return company.partner_id.image_1920
        return False

    def _thermal_prices_include_taxes(self):
        """Whether the receipt prints line prices with taxes included.

        False keeps the generic behaviour: net prices, a subtotal and the tax
        breakdown. Localization modules override it when the document, or the
        customer, is not meant to see the tax discriminated, and then the
        subtotal and the breakdown are dropped because the tax is already in
        every price.
        """
        self.ensure_one()
        return False
