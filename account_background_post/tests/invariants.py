##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################


class BackgroundPostInvariants:
    """Batería de invariantes del circuito de validación en background.

    Valen después de cualquier operación del circuito — no son el assert específico de ningún
    escenario. Los módulos que dependen de account_background_post heredan esta clase para
    correrlas en sus propias suites.

    Sin interruptores: un escenario que viole legítimamente una invariante lo declara en el
    test, a la vista y con el motivo al lado.
    """

    def assert_background_post_invariants(self, moves):
        self.assert_no_background_state_on_posted(moves)
        self.assert_attempts_are_scheduled(moves)
        self.assert_attempts_within_limit(moves)
        self.assert_internal_recipients_are_internal(moves)

    def assert_no_background_state_on_posted(self, moves):
        # Una factura que salió del borrador no puede conservar estado de background.
        for move in moves.filtered(lambda m: m.state != "draft"):
            self.assertFalse(move.background_post, "%s ya no está en borrador y sigue marcada" % move.id)
            self.assertFalse(move.background_post_date, "%s ya no está en borrador y conserva la fecha" % move.id)
            self.assertEqual(move.background_post_attempts, 0, "%s conserva intentos ya validada" % move.id)

    def assert_attempts_are_scheduled(self, moves):
        # Un contador de intentos vivo siempre tiene marca y fecha: sin fecha el cron la
        # reintentaría en cada corrida, sin esperar el delay.
        for move in moves.filtered("background_post_attempts"):
            self.assertTrue(move.background_post, "%s acumula intentos y no está marcada" % move.id)
            self.assertTrue(move.background_post_date, "%s acumula intentos y no tiene fecha" % move.id)

    def assert_attempts_within_limit(self, moves):
        # Los intentos nunca pasan el tope configurado.
        max_retries = self.env["account.move"]._get_background_post_max_retries()
        for move in moves:
            self.assertLessEqual(move.background_post_attempts, max_retries, "%s pasó el tope de reintentos" % move.id)

    def assert_internal_recipients_are_internal(self, moves):
        # El chatter de una factura tiene al cliente entre sus seguidores: si el filtro de
        # destinatarios se afloja, el aviso de un error interno se le manda al cliente.
        for partner in moves.sudo().get_internal_partners():
            self.assertTrue(partner.user_ids, "%s no tiene usuario y quedó como destinatario" % partner.id)
            self.assertFalse(
                any(user.share for user in partner.user_ids),
                "%s es externo y quedó como destinatario del aviso" % partner.id,
            )
