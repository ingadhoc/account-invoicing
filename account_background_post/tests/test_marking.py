##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from datetime import timedelta

from odoo import Command, fields
from odoo.tests import tagged

from .common import BackgroundPostCommon


@tagged("post_install", "-at_install")
class TestBackgroundPostMarking(BackgroundPostCommon):
    def test_wizard_marks_only_the_drafts(self):
        """Comportamientos 1 y 13 del relevamiento: el wizard marca los borradores de la
        selección y no toca lo que ya está validado."""
        draft = self._create_bg_invoice()
        posted = self._create_bg_invoice()
        posted.action_post()
        # con fecha vieja puesta, para verificar que marcar de nuevo empieza de cero
        draft.background_post_date = fields.Datetime.now() + timedelta(days=7)

        wizard = self.env["validate.account.move"].create({"move_ids": [Command.set((draft + posted).ids)]})
        wizard.action_background_post()

        self.assertTrue(draft.background_post)
        self.assertFalse(draft.background_post_date, "marcar desde el wizard es validar en la próxima corrida")
        self.assertFalse(posted.background_post)
        self.assert_background_post_invariants(draft + posted)

    def test_context_defers_only_sale_documents(self):
        """Comportamiento 12 del relevamiento y acceptance criteria de la spec de ecommerce:
        el contexto difiere facturas y notas de crédito de cliente; el resto valida normal."""
        for move_type, deferred in (("out_invoice", True), ("out_refund", True), ("in_invoice", False)):
            with self.subTest(move_type=move_type):
                move = self._create_bg_invoice(move_type=move_type)
                move.with_context(force_background_post=True).action_post()
                self.assertEqual(move.background_post, deferred)
                self.assertEqual(move.state, "draft" if deferred else "posted")
                self.assert_background_post_invariants(move)

    def test_context_accepts_a_posting_date(self):
        """Comportamiento 12: el contexto puede traer la fecha en la que hay que validar."""
        move = self._create_bg_invoice()
        post_at = fields.Datetime.now() + timedelta(days=1)
        move.with_context(force_background_post=post_at).action_post()
        self.assertEqual(move.state, "draft")
        self.assertEqual(move.background_post_date, post_at)

    def test_context_true_clears_a_stale_date(self):
        """Comportamiento 12: True significa "en la próxima corrida", así que no puede heredar
        una fecha de una programación anterior."""
        move = self._create_bg_invoice()
        # la fecha vieja se pone a mano: armarla con _schedule_background_post haría que el test
        # dependa del mismo método que verifica, y pasaría en verde con el reset roto
        move.write({"background_post": True, "background_post_date": fields.Datetime.now() + timedelta(days=7)})
        move.with_context(force_background_post=True).action_post()
        self.assertTrue(move.background_post)
        self.assertFalse(move.background_post_date)
