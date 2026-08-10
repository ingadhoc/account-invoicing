##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError

from .invariants import BackgroundPostInvariants


class BackgroundPostCommon(AccountTestInvoicingCommon, BackgroundPostInvariants):
    """Configuración de los escenarios del circuito de background.

    El entorno (plan de cuentas, diarios, impuestos) sale de la base vía la clase de account;
    los usuarios, los parámetros y los documentos los crea el test.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # El interno es el usuario con el que corre la suite: es interno por construcción y no
        # depende de crear usuarios, que Odoo 19 deja inactivos si se los crea así.
        cls.internal_partner = cls.env.user.partner_id
        # El externo es un usuario de portal (share=True), como el cliente de una factura real.
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "background_post_customer",
                "login": "background_post_customer",
                "company_id": cls.env.company.id,
                "company_ids": [Command.set(cls.env.company.ids)],
                "group_ids": [Command.set([cls.env.ref("base.group_portal").id])],
            }
        )
        cls.external_partner = cls.portal_user.partner_id

    def _create_bg_invoice(self, **kwargs):
        kwargs.setdefault("price_unit", 100.0)
        kwargs.setdefault("tax_ids", [])
        return self._create_invoice_one_line(**kwargs)

    def _set_param(self, key, value):
        self.env["ir.config_parameter"].sudo().set_param("account_background_post.%s" % key, value)

    def _open_validate_wizard(self, moves):
        return (
            self.env["validate.account.move"].with_context(active_model="account.move", active_ids=moves.ids).create({})
        )

    @contextmanager
    def _neutralized_cursor(self, tolerate_rollback=False):
        """El cron commitea después de cada factura y hace rollback ante un error; el cursor de
        test prohíbe las dos cosas."""
        with ExitStack() as stack:
            stack.enter_context(patch.object(self.env.cr, "commit", self.env.flush_all))
            if tolerate_rollback:
                stack.enter_context(patch.object(self.env.cr, "rollback", lambda: None))
            yield

    @contextmanager
    def _failing_post(self, moves, error="ARCA no responde"):
        """Hace fallar action_post solo en esas facturas, antes de que toquen nada."""
        model = self.env["account.move"].__class__
        original = model.action_post
        broken_ids = set(moves.ids)

        def action_post(self):
            if broken_ids & set(self.ids):
                raise UserError(error)
            return original(self)

        with patch.object(model, "action_post", action_post):
            yield

    def _add_followers(self, move, partners):
        # Directo sobre mail.followers: message_subscribe depende de los subtipos por defecto del
        # modelo y en account.move deja afuera al partner interno.
        self.env["mail.followers"].sudo().create(
            [{"res_model": move._name, "res_id": move.id, "partner_id": partner.id} for partner in partners]
        )

    def _run_cron(self, moves, tolerate_rollback=False):
        """Corre el cron y verifica la batería de invariantes sobre lo que tocó.

        Con sudo porque el ir.cron corre como root: con el usuario de la suite, el circuito no
        ve los usuarios internos y el escenario dejaría de parecerse a producción."""
        with self._neutralized_cursor(tolerate_rollback=tolerate_rollback):
            self.env["account.move"].sudo()._cron_background_post_invoices()
        self.assert_background_post_invariants(moves)

    def _background_post_messages(self, move):
        return move.sudo().message_ids.filtered(lambda m: "background" in (m.body or ""))
