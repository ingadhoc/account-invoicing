from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountInvoiceTax(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_tax = cls.env["account.tax"].create(
            {
                "name": "VAT Purchase 21",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "purchase",
                "company_id": cls.env.company.id,
            }
        )
        cls.sale_tax = cls.env["account.tax"].create(
            {
                "name": "VAT Sale 21",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "sale",
                "company_id": cls.env.company.id,
            }
        )
        cls.fixed_tax = cls.env["account.tax"].create(
            {
                "name": "Fixed Tax 1",
                "amount_type": "fixed",
                "amount": 1.0,
                "type_tax_use": "purchase",
                "company_id": cls.env.company.id,
            }
        )
        cls.not_taxed_tax = cls.env["account.tax"].create(
            {
                "name": "VAT Not Taxed",
                "amount_type": "fixed",
                "amount": 0.0,
                "type_tax_use": "purchase",
                "company_id": cls.env.company.id,
            }
        )

    def _build_move(self, move_type, taxes):
        return self._create_invoice_one_line(
            move_type=move_type,
            price_unit=1000.0,
            tax_ids=taxes,
        )

    def _open_wizard(self, move):
        return (
            self.env["account.invoice.tax"]
            .with_context(
                active_model="account.move",
                active_ids=move.ids,
            )
            .create({})
        )

    def _make_wizard(self, move, lines_vals):
        return (
            self.env["account.invoice.tax"]
            .with_context(
                active_model="account.move",
                active_ids=move.ids,
            )
            .create(
                {
                    "move_id": move.id,
                    "tax_line_ids": [Command.create(v) for v in lines_vals],
                }
            )
        )

    def _tax_line(self, move, tax):
        return move.line_ids.filtered(lambda l: l.tax_line_id == tax)

    def _set_amount_and_apply(self, move, amount, tax=None):
        wizard = self._open_wizard(move)
        wizard.tax_line_ids.amount = amount
        wizard.action_update_tax()
        return self._tax_line(move, tax or self.purchase_tax)

    def test_in_invoice_positive_amount(self):
        move = self._build_move("in_invoice", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, 100.0)
        self.assertEqual(tax_line.debit, 100.0)
        self.assertEqual(tax_line.credit, 0.0)
        self.assertEqual(tax_line.balance, 100.0)
        self.assertEqual(tax_line.amount_currency, 100.0)

    def test_in_invoice_negative_amount_keeps_negative(self):
        """Ticket #116742: cargar -100 en wizard sobre in_invoice debe
        preservar el signo negativo en balance y amount_currency."""
        move = self._build_move("in_invoice", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, -100.0)
        self.assertEqual(tax_line.debit, 0.0)
        self.assertEqual(tax_line.credit, 100.0)
        self.assertEqual(tax_line.balance, -100.0)
        self.assertEqual(tax_line.amount_currency, -100.0)

    def test_in_refund_positive_amount(self):
        move = self._build_move("in_refund", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, 100.0)
        self.assertEqual(tax_line.debit, 0.0)
        self.assertEqual(tax_line.credit, 100.0)
        self.assertEqual(tax_line.balance, -100.0)
        self.assertEqual(tax_line.amount_currency, -100.0)

    def test_in_refund_negative_amount_keeps_positive(self):
        move = self._build_move("in_refund", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, -100.0)
        self.assertEqual(tax_line.debit, 100.0)
        self.assertEqual(tax_line.credit, 0.0)
        self.assertEqual(tax_line.balance, 100.0)
        self.assertEqual(tax_line.amount_currency, 100.0)

    def test_wizard_raises_on_out_invoice(self):
        move = self._build_move("out_invoice", self.sale_tax)
        with self.assertRaises(UserError):
            self._open_wizard(move)

    def test_wizard_raises_on_out_refund(self):
        move = self._build_move("out_refund", self.sale_tax)
        with self.assertRaises(UserError):
            self._open_wizard(move)

    def test_wizard_amount_is_applied_to_accounting_entry(self):
        """El monto ingresado en el wizard se refleja en el apunte contable
        y se persiste en tax_override_data para impuestos fijos."""
        move = self._build_move("in_invoice", self.fixed_tax)
        tax_line = self._set_amount_and_apply(move, 750.0, tax=self.fixed_tax)

        self.assertAlmostEqual(abs(tax_line.balance), 750.0)
        self.assertAlmostEqual(move.tax_override_data[str(self.fixed_tax.id)]["amount"], 750.0)

    def test_override_survives_price_change_and_new_line(self):
        """El override del impuesto fijo sobrevive tanto a un cambio de precio
        como al agregado de una nueva línea en la factura."""
        move = self._build_move("in_invoice", self.fixed_tax)
        self._set_amount_and_apply(move, 320.0, tax=self.fixed_tax)

        # Cambio de precio → dispara recomputación de líneas de impuesto
        move.invoice_line_ids[0].write({"price_unit": 2000.0})
        self.assertAlmostEqual(
            abs(self._tax_line(move, self.fixed_tax).balance),
            320.0,
            msg="Override lost after price change",
        )

        # Agregar línea nueva → segunda recomputación
        move.write(
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Extra line",
                            "quantity": 1.0,
                            "price_unit": 500.0,
                            "account_id": self.company_data["default_account_expense"].id,
                            "tax_ids": [Command.set(self.fixed_tax.ids)],
                        }
                    )
                ]
            }
        )
        self.assertAlmostEqual(
            abs(self._tax_line(move, self.fixed_tax).balance),
            320.0,
            msg="Override lost after adding a new line",
        )

    def test_percent_tax_applied_to_entry_but_not_persisted(self):
        """El override de un impuesto porcentual se aplica al apunte contable
        pero no se persiste en tax_override_data (siempre se recomputa)."""
        # Se usa 150 en lugar del valor natural (21% de 1000 = 210) para
        # distinguir el override del cómputo automático.
        move = self._build_move("in_invoice", self.purchase_tax)
        tax_line = self._set_amount_and_apply(move, 150.0)

        self.assertAlmostEqual(abs(tax_line.balance), 150.0)
        self.assertNotIn(str(self.purchase_tax.id), move.tax_override_data or {})

    def test_override_survives_fixed_tax_netting_to_zero(self):
        """Percepción de importe fijo sobre una línea positiva y una negativa
        que la cancelan: el core borra la línea de impuesto en cero y el
        override quedaba huérfano, así que el asiento se registraba sin la
        percepción mientras el widget de totales sí la mostraba (ticket 124374).
        """
        move = self._build_move("in_invoice", self.fixed_tax)
        move.write(
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Bonificación 11 %",
                            "quantity": 1.0,
                            "price_unit": -110.0,
                            "account_id": self.company_data["default_account_expense"].id,
                            "tax_ids": [Command.set(self.fixed_tax.ids)],
                        }
                    )
                ]
            }
        )
        self._set_amount_and_apply(move, 155.2, tax=self.fixed_tax)

        tax_line = self._tax_line(move, self.fixed_tax)
        self.assertTrue(tax_line, "The tax line was dropped, the override is lost")
        self.assertAlmostEqual(abs(tax_line.balance), 155.2)
        # El asiento tiene que coincidir con el total mostrado al usuario.
        self.assertAlmostEqual(move.amount_untaxed, 890.0)
        self.assertAlmostEqual(move.amount_total, 1045.2)
        payment_term_line = move.line_ids.filtered(lambda l: l.display_type == "payment_term")
        self.assertAlmostEqual(abs(payment_term_line.balance), 1045.2)

        # Al confirmar, la deuda con el proveedor tiene que ser el total.
        move.invoice_date = fields.Date.context_today(move)
        move.action_post()
        self.assertAlmostEqual(move.amount_total, 1045.2)
        self.assertAlmostEqual(move.amount_residual, 1045.2)

    def test_zero_amount_tax_is_kept_on_the_product_line(self):
        """Factura con una línea al 21 % y otra con "IVA No Gravado" (impuesto
        de importe fijo en cero): ajustar los centavos del IVA desde el wizard
        borraba el No Gravado de su línea de producto (ticket 126379).  El
        impuesto no tiene línea en el asiento (vale cero y no tiene override),
        así que ``default_get`` no lo trae al wizard y el wizard no lo toca.
        Si después se le carga un importe, no se agrega a la línea al 21 %.
        """
        invoice = self._build_move("in_invoice", self.purchase_tax)
        invoice.write(
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Concepto no gravado",
                            "quantity": 1.0,
                            "price_unit": 500.0,
                            "account_id": self.company_data["default_account_expense"].id,
                            "tax_ids": [Command.set(self.not_taxed_tax.ids)],
                        }
                    )
                ]
            }
        )
        not_taxed_line = invoice.invoice_line_ids.filtered(lambda l: l.price_unit == 500.0)

        self.assertFalse(self._tax_line(invoice, self.not_taxed_tax))
        # El wizard se abre solo con el IVA, tal como lo arma ``default_get``.
        self._make_wizard(
            invoice, [{"tax_id": self.purchase_tax.id, "amount": 210.97, "new_tax": False}]
        ).action_update_tax()

        self.assertIn(
            self.not_taxed_tax,
            not_taxed_line.tax_ids,
            "The zero-amount tax was unlinked from its product line",
        )
        self.assertNotIn(
            self.not_taxed_tax, invoice.invoice_line_ids.filtered(lambda l: l.price_unit == 1000.0).tax_ids
        )
        self.assertAlmostEqual(abs(self._tax_line(invoice, self.purchase_tax).balance), 210.97)
        self.assertAlmostEqual(invoice.amount_untaxed, 1500.0)
        self.assertAlmostEqual(invoice.amount_total, 1710.97)

        self._make_wizard(
            invoice,
            [
                {"tax_id": self.purchase_tax.id, "amount": 210.97, "new_tax": False},
                {"tax_id": self.not_taxed_tax.id, "amount": 45.0, "new_tax": True},
            ],
        ).action_update_tax()
        self.assertEqual(invoice.invoice_line_ids.filtered(lambda l: l.price_unit == 1000.0).tax_ids, self.purchase_tax)
        self.assertAlmostEqual(abs(self._tax_line(invoice, self.not_taxed_tax).balance), 45.0)

    def test_zero_fixed_tax_without_override_has_no_tax_line(self):
        """Factura de proveedor con "IVA Exento" configurado como impuesto fijo
        de importe cero: no tiene que generar un apunte de impuesto 0/0, que
        después aparece en el Libro mayor aunque se oculten las líneas en 0
        (ticket 128734).  Si se le carga un importe desde el wizard, la línea sí
        tiene que existir para que el importe llegue al asiento.
        """
        invoice = self._build_move("in_invoice", self.not_taxed_tax)
        self.assertFalse(self._tax_line(invoice, self.not_taxed_tax))

        invoice.invoice_date = fields.Date.context_today(invoice)
        invoice.action_post()
        self.assertFalse(invoice.line_ids.filtered(lambda l: l.display_type == "tax"))

        overridden = self._build_move("in_invoice", self.not_taxed_tax)
        self._make_wizard(
            overridden, [{"tax_id": self.not_taxed_tax.id, "amount": 45.0, "new_tax": False}]
        ).action_update_tax()
        self.assertAlmostEqual(abs(self._tax_line(overridden, self.not_taxed_tax).balance), 45.0)
        self.assertAlmostEqual(overridden.amount_total, 1045.0)

    def test_manual_amount_on_zero_fixed_tax_next_to_percent_tax(self):
        """Factura con IVA 21 % y una percepción fija de importe cero en la
        misma línea: el wizard no trae la percepción (no tiene apunte), así que
        se agrega como línea nueva con 45.  El importe tiene que llegar al
        asiento sin mover el IVA (ticket 128734).
        """
        invoice = self._build_move("in_invoice", self.purchase_tax + self.not_taxed_tax)
        self.assertFalse(self._tax_line(invoice, self.not_taxed_tax))

        self._make_wizard(
            invoice,
            [
                {"tax_id": self.purchase_tax.id, "amount": 210.0, "new_tax": False},
                {"tax_id": self.not_taxed_tax.id, "amount": 45.0, "new_tax": True},
            ],
        ).action_update_tax()

        self.assertAlmostEqual(abs(self._tax_line(invoice, self.not_taxed_tax).balance), 45.0)
        self.assertAlmostEqual(abs(self._tax_line(invoice, self.purchase_tax).balance), 210.0)
        self.assertAlmostEqual(invoice.amount_total, 1255.0)
        invoice.invoice_date = fields.Date.context_today(invoice)
        invoice.action_post()
        self.assertAlmostEqual(abs(self._tax_line(invoice, self.not_taxed_tax).balance), 45.0)
        self.assertAlmostEqual(invoice.amount_total, 1255.0)

    def test_fixed_tax_deliberately_set_to_zero_is_respected(self):
        """Un impuesto fijo con importe (1 por unidad) que se deja en 0 desde el
        wizard queda en 0: no vuelve a su importe al cambiar el precio ni al
        publicar, y sigue en la línea de producto.
        """
        invoice = self._build_move("in_invoice", self.fixed_tax)
        self.assertAlmostEqual(invoice.amount_total, 1001.0)
        self._make_wizard(invoice, [{"tax_id": self.fixed_tax.id, "amount": 0.0, "new_tax": False}]).action_update_tax()
        self.assertAlmostEqual(invoice.amount_total, 1000.0)

        invoice.invoice_line_ids[0].write({"quantity": 3.0})
        self.assertAlmostEqual(sum(self._tax_line(invoice, self.fixed_tax).mapped("balance")), 0.0)
        self.assertAlmostEqual(invoice.amount_total, 3000.0)

        invoice.invoice_date = fields.Date.context_today(invoice)
        invoice.action_post()
        self.assertIn(self.fixed_tax, invoice.invoice_line_ids.tax_ids)
        self.assertAlmostEqual(sum(self._tax_line(invoice, self.fixed_tax).mapped("balance")), 0.0)
        self.assertAlmostEqual(invoice.amount_total, 3000.0)

    def test_manual_amount_on_zero_fixed_tax_set_back_to_zero(self):
        """Un impuesto fijo de importe cero al que se le cargó 45 desde el
        wizard y después se lo vuelve a dejar en 0: el apunte 0/0 no queda en el
        asiento y el impuesto sigue en la línea de producto (ticket 128734).
        """
        invoice = self._build_move("in_invoice", self.not_taxed_tax)
        self._make_wizard(
            invoice, [{"tax_id": self.not_taxed_tax.id, "amount": 45.0, "new_tax": False}]
        ).action_update_tax()
        self.assertAlmostEqual(invoice.amount_total, 1045.0)

        self._make_wizard(
            invoice, [{"tax_id": self.not_taxed_tax.id, "amount": 0.0, "new_tax": False}]
        ).action_update_tax()
        self.assertFalse(self._tax_line(invoice, self.not_taxed_tax))
        self.assertAlmostEqual(invoice.amount_total, 1000.0)

        invoice.invoice_line_ids[0].write({"price_unit": 2000.0})
        invoice.invoice_date = fields.Date.context_today(invoice)
        invoice.action_post()
        self.assertIn(self.not_taxed_tax, invoice.invoice_line_ids.tax_ids)
        self.assertFalse(self._tax_line(invoice, self.not_taxed_tax))
        self.assertAlmostEqual(invoice.amount_total, 2000.0)

    def test_zero_fixed_tax_set_back_to_zero_next_to_percent_tax(self):
        """IVA 21 % y una percepción fija de importe cero: se le carga 45 a la
        percepción, después se la vuelve a 0 y se publica sin tocar nada más.
        No tiene que quedar el apunte 0/0 de la percepción y el IVA no se mueve
        (ticket 128734).
        """
        invoice = self._build_move("in_invoice", self.purchase_tax + self.not_taxed_tax)
        self._make_wizard(
            invoice,
            [
                {"tax_id": self.purchase_tax.id, "amount": 210.0, "new_tax": False},
                {"tax_id": self.not_taxed_tax.id, "amount": 45.0, "new_tax": True},
            ],
        ).action_update_tax()
        self.assertAlmostEqual(invoice.amount_total, 1255.0)

        self._make_wizard(
            invoice,
            [
                {"tax_id": self.purchase_tax.id, "amount": 210.0, "new_tax": False},
                {"tax_id": self.not_taxed_tax.id, "amount": 0.0, "new_tax": False},
            ],
        ).action_update_tax()
        invoice.invoice_date = fields.Date.context_today(invoice)
        invoice.action_post()
        self.assertFalse(self._tax_line(invoice, self.not_taxed_tax))
        self.assertIn(self.not_taxed_tax, invoice.invoice_line_ids.tax_ids)
        self.assertAlmostEqual(abs(self._tax_line(invoice, self.purchase_tax).balance), 210.0)
        self.assertAlmostEqual(invoice.amount_total, 1210.0)
