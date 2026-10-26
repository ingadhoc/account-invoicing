##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import BackgroundPostCommon


@tagged("post_install", "-at_install")
class TestListConfirmation(BackgroundPostCommon):
    """Confirmar desde la lista tiene que pasar por action_post, igual que de a una.

    El resto de la suite abre el wizard con active_ids, que es como lo abría Odoo 18. En 19 la
    acción de lista lo construye con create({'move_ids': ...}), y por ese camino el wizard
    quedaba con count_inv en 0: validate_move caía en la rama nativa, que postea con _post() y
    se saltea todo lo que cuelga de action_post (ticket 131217).
    """

    def _confirm_from_list(self, moves):
        """Recorre lo que hace Acción > Confirmar asientos y devuelve el wizard que abre."""
        action = moves.action_validate_moves_with_confirmation()
        self.assertEqual(
            action.get("res_model"),
            "validate.account.move",
            "el módulo fuerza el wizard para toda factura, así que la acción tiene que abrirlo",
        )
        return self.env["validate.account.move"].browse(action["res_id"])

    def test_count_inv_counts_the_moves_the_wizard_holds(self):
        """Control directo del campo: es lo que decide por qué rama sale validate_move."""
        invoices = self._create_bg_invoice() + self._create_bg_invoice()

        wizard = self._confirm_from_list(invoices)

        self.assertEqual(wizard.move_ids, invoices)
        self.assertEqual(wizard.count_inv, 2, "el contador tiene que seguir a move_ids")

    def test_list_confirmation_goes_through_action_post(self):
        """Control de comportamiento: si vuelve la rama nativa, action_post deja de correr y
        todo lo que cuelga de él (el cobro automático del tipo de pedido, el mail del diario)
        se pierde sin ningún error."""
        invoices = self._create_bg_invoice() + self._create_bg_invoice()
        posted_by_action_post = []

        action_post_original = type(invoices).action_post

        def spy(self_moves):
            posted_by_action_post.extend(self_moves.ids)
            return action_post_original(self_moves)

        self.patch(type(invoices), "action_post", spy)

        wizard = self._confirm_from_list(invoices)
        with self._neutralized_cursor():
            wizard.validate_move_confirm()

        self.assertEqual(set(invoices.mapped("state")), {"posted"})
        self.assertEqual(
            sorted(posted_by_action_post),
            sorted(invoices.ids),
            "cada factura del lote tiene que pasar por action_post",
        )
        self.assert_background_post_invariants(invoices)

    def test_batch_size_guard_applies_from_the_list(self):
        """El tope de lote vivía detrás del mismo count_inv, así que por este camino tampoco
        saltaba: se podían confirmar de golpe más facturas que las permitidas."""
        invoices = self._create_bg_invoice() + self._create_bg_invoice()
        self._set_param("batch_size", "1")

        wizard = self._confirm_from_list(invoices)

        with self._neutralized_cursor(), self.assertRaises(UserError):
            wizard.validate_move_confirm()
        self.assertEqual(set(invoices.mapped("state")), {"draft"})
