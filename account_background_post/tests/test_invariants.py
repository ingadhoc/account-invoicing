##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged

from .common import BackgroundPostCommon


@tagged("post_install", "-at_install")
class TestBackgroundPostInvariants(BackgroundPostCommon):
    """Cada invariante de la batería, en los dos sentidos: que no moleste con una operación
    sana, y que detecte el estado defectuoso para el que existe."""

    def test_no_background_state_on_posted(self):
        invoice = self._create_bg_invoice()
        invoice._schedule_background_post()
        # operación sana: el cron la valida y limpia el estado
        self._run_cron(invoice)
        self.assert_no_background_state_on_posted(invoice)

        # defectuosa: validada y todavía marcada
        invoice.background_post = True
        with self.assertRaises(AssertionError):
            self.assert_no_background_state_on_posted(invoice)

    def test_attempts_are_scheduled(self):
        self._set_param("max_retries", "2")
        invoice = self._create_bg_invoice()
        invoice._schedule_background_post()
        # sana: reprogramar deja marca y fecha
        invoice._reschedule_background_post()
        self.assert_attempts_are_scheduled(invoice)

        # defectuosa: contador vivo sin fecha, que el cron reintentaría en cada corrida
        invoice.background_post_date = False
        with self.assertRaises(AssertionError):
            self.assert_attempts_are_scheduled(invoice)

    def test_attempts_within_limit(self):
        self._set_param("max_retries", "1")
        invoice = self._create_bg_invoice()
        invoice._schedule_background_post()
        # sana: un reintento con tope 1
        invoice._reschedule_background_post()
        self.assert_attempts_within_limit(invoice)

        # defectuosa: más intentos que el tope
        invoice.background_post_attempts = 5
        with self.assertRaises(AssertionError):
            self.assert_attempts_within_limit(invoice)

    def test_internal_recipients_are_internal(self):
        invoice = self._create_bg_invoice()
        self._add_followers(invoice, self.internal_partner + self.external_partner)
        # sana: el filtro deja afuera al cliente
        self.assert_internal_recipients_are_internal(invoice)
        self.assertEqual(invoice.sudo().get_internal_partners(), self.internal_partner)

        # defectuosa: el filtro aflojado devuelve a todos los seguidores
        model = self.env["account.move"].__class__
        with patch.object(model, "get_internal_partners", lambda self: self.message_partner_ids):
            with self.assertRaises(AssertionError):
                self.assert_internal_recipients_are_internal(invoice)

    def test_battery_runs_after_a_scheduled_posting(self):
        # La batería completa sobre el camino normal: no molesta a una operación sana.
        invoice = self._create_bg_invoice()
        invoice._schedule_background_post(fields.Datetime.now())
        self._run_cron(invoice)
        self.assertEqual(invoice.state, "posted")
