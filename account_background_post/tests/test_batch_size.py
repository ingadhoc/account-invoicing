##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import BackgroundPostCommon


@tagged("post_install", "-at_install")
class TestBackgroundPostBatchSize(BackgroundPostCommon):
    def test_batch_size_guard(self):
        """Comportamientos 2 y 3 del relevamiento: un lote más grande que el tope obliga a usar
        background — control positivo: si el bloqueo se pierde, el usuario vuelve a colgar la
        sesión validando de más."""
        invoices = self._create_bg_invoice() + self._create_bg_invoice()

        with self.subTest("un lote más grande que el tope se bloquea"):
            self._set_param("batch_size", "1")
            wizard = self._open_validate_wizard(invoices)
            # el cursor neutralizado deja que el rojo caiga en el bloqueo y no en el commit
            with self._neutralized_cursor(), self.assertRaises(UserError):
                wizard.validate_move()
            self.assertEqual(set(invoices.mapped("state")), {"draft"})

        with self.subTest("un lote dentro del tope se valida de a una"):
            self._set_param("batch_size", "5")
            wizard = self._open_validate_wizard(invoices)
            with self._neutralized_cursor():
                wizard.validate_move()
            self.assertEqual(set(invoices.mapped("state")), {"posted"})
            self.assert_background_post_invariants(invoices)
