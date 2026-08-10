##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged

from .common import BackgroundPostCommon


@tagged("post_install", "-at_install")
class TestBackgroundPostCron(BackgroundPostCommon):
    def test_cron_respects_the_schedule(self):
        """Comportamientos 4, 5, 6 y 11 del relevamiento: qué hace el cron con la fecha
        programada, y qué queda cuando la factura se valida a mano."""
        invoice = self._create_bg_invoice()

        with self.subTest("sin fecha, se valida en la próxima corrida"):
            invoice._schedule_background_post()
            self._run_cron(invoice)
            self.assertEqual(invoice.state, "posted")

        with self.subTest("con fecha futura, espera"):
            scheduled = self._create_bg_invoice()
            scheduled._schedule_background_post(fields.Datetime.now() + timedelta(hours=1))
            self._run_cron(scheduled)
            self.assertEqual(scheduled.state, "draft")
            self.assertTrue(scheduled.background_post_date)

        with self.subTest("una vez vencida la fecha, se valida"):
            scheduled.background_post_date = fields.Datetime.now() - timedelta(minutes=1)
            self._run_cron(scheduled)
            self.assertEqual(scheduled.state, "posted")

        with self.subTest("validarla a mano saca la programación"):
            manual = self._create_bg_invoice()
            manual._schedule_background_post(fields.Datetime.now() + timedelta(days=1))
            manual.action_post()
            self.assertEqual(manual.state, "posted")
            self.assert_background_post_invariants(manual)

    def test_healthy_invoices_are_posted_before_the_rescheduled_ones(self):
        """Comportamiento 9: las facturas sin fecha van primero, y las programadas de la más
        vieja a la más nueva, para que una tanda que falla no le coma el turno a las sanas."""
        older = self._create_bg_invoice()
        newer = self._create_bg_invoice()
        healthy = self._create_bg_invoice()
        older._schedule_background_post(fields.Datetime.now() - timedelta(hours=2))
        newer._schedule_background_post(fields.Datetime.now() - timedelta(hours=1))
        healthy._schedule_background_post()

        # el orden observable es el orden en que el cron las valida
        posted_order = []
        model = self.env["account.move"].__class__
        original = model.action_post

        def action_post(this):
            posted_order.extend(this.ids)
            return original(this)

        with patch.object(model, "action_post", action_post):
            self._run_cron(healthy + older + newer)

        self.assertEqual(posted_order, (healthy + older + newer).ids)
