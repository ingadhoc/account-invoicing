##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import fields
from odoo.service.model import MAX_TRIES_ON_CONCURRENCY_FAILURE
from odoo.tests import tagged
from odoo.tools import mute_logger
from psycopg2 import errors

from .common import BackgroundPostCommon


@tagged("post_install", "-at_install")
class TestBackgroundPostFailure(BackgroundPostCommon):
    @mute_logger("odoo.addons.account_background_post.models.account_move")
    def test_failure_notifies_internals_and_retries(self):
        """Comportamientos 7, 8 y 10 del relevamiento: qué pasa cuando la validación falla, a
        quién se le avisa, y que una factura rota no frene a las sanas."""
        self._set_param("max_retries", "0")
        self._set_param("retry_delay_minutes", "0")
        broken = self._create_bg_invoice()
        healthy = self._create_bg_invoice()
        # el cliente es seguidor de la factura, como en cualquier factura real
        self._add_followers(broken, self.internal_partner + self.external_partner)

        with self.subTest("sin reintentos, la primera falla la desmarca y avisa solo a internos"):
            (broken + healthy)._schedule_background_post()
            with self._failing_post(broken):
                self._run_cron(broken + healthy, tolerate_rollback=True)
            self.assertEqual(broken.state, "draft")
            self.assertFalse(broken.background_post)
            self.assertEqual(broken.background_post_attempts, 0)
            messages = self._background_post_messages(broken)
            self.assertEqual(len(messages), 1, "el aviso al desmarcar tiene que ser uno solo")
            self.assertEqual(messages.partner_ids, self.internal_partner)
            self.assertEqual(healthy.state, "posted", "una factura rota no puede frenar a las sanas")

        self._set_param("max_retries", "2")
        retried = self._create_bg_invoice()
        retried._schedule_background_post()

        with self.subTest("con reintentos disponibles, reprograma y no avisa"):
            for attempt in (1, 2):
                with self._failing_post(retried):
                    self._run_cron(retried, tolerate_rollback=True)
                self.assertTrue(retried.background_post)
                self.assertEqual(retried.background_post_attempts, attempt)
                self.assertFalse(self._background_post_messages(retried))

        with self.subTest("agotados los reintentos, la desmarca y avisa una sola vez"):
            with self._failing_post(retried):
                self._run_cron(retried, tolerate_rollback=True)
            self.assertFalse(retried.background_post)
            self.assertFalse(retried.background_post_date)
            self.assertEqual(retried.background_post_attempts, 0)
            self.assertEqual(len(self._background_post_messages(retried)), 1)

    @mute_logger("odoo.addons.account_background_post.models.account_move")
    def test_concurrency_failure_retries_without_notifying(self):
        """Un choque de concurrencia se resuelve solo al reintentar: sin reintentos configurados,
        la factura se reprograma para la próxima corrida y solo avisa si choca hasta el tope."""
        self._set_param("max_retries", "0")
        self._set_param("retry_delay_minutes", "30")
        move = self._create_bg_invoice()
        self._add_followers(move, self.internal_partner)
        move._schedule_background_post()
        conflict = errors.SerializationFailure("could not serialize access due to concurrent update")

        with self.subTest("el choque reprograma para la próxima corrida, sin esperar ni avisar"):
            with self._failing_post(move, conflict):
                self._run_cron(move, tolerate_rollback=True)
            self.assertTrue(move.background_post)
            self.assertEqual(move.background_post_attempts, 1)
            self.assertLessEqual(move.background_post_date, fields.Datetime.now())
            self.assertFalse(self._background_post_messages(move))

        with self.subTest("la corrida siguiente la valida"):
            self._run_cron(move)
            self.assertEqual(move.state, "posted")
            self.assertFalse(move.background_post)

        stuck = self._create_bg_invoice()
        self._add_followers(stuck, self.internal_partner)
        stuck._schedule_background_post()
        deadlock = errors.DeadlockDetected("deadlock detected")

        with self.subTest("si choca hasta el tope, la desmarca y avisa una sola vez"):
            for _attempt in range(MAX_TRIES_ON_CONCURRENCY_FAILURE):
                with self._failing_post(stuck, deadlock):
                    self._run_cron(stuck, tolerate_rollback=True)
                self.assertFalse(self._background_post_messages(stuck))
            with self._failing_post(stuck, deadlock):
                self._run_cron(stuck, tolerate_rollback=True)
            self.assertFalse(stuck.background_post)
            self.assertEqual(stuck.state, "draft")
            self.assertEqual(len(self._background_post_messages(stuck)), 1)
