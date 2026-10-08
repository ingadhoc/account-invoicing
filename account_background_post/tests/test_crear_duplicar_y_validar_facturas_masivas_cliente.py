from datetime import date

from odoo.tests.common import TransactionCase


class TestCrearDuplicarYValidarFacturasMasivasCliente(TransactionCase):
    def setUp(self):
        super().setUp()

        # Creación del Cliente
        self.cliente = self.env["res.partner"].create(
            {
                "name": "ADHOC SA",
                "vat": "30714295698",
                "is_company": True,
            }
        )

        # Usar un producto existente o crear uno con los valores por defecto necesarios
        self.producto = self.env["product.product"].search([("type", "=", "service")], limit=1)
        if not self.producto:
            # Crear plantilla de producto primero
            template = self.env["product.template"].create(
                {
                    "name": "Servicio de Test",
                    "list_price": 100.00,
                    "type": "service",
                }
            )
            self.producto = template.product_variant_ids[0]

    def test_crear_duplicar_y_validar_facturas_masivas_cliente(self):
        """
        Validar la funcionalidad backend principal del flujo de gestión de Facturas de Cliente.
        El test simula la creación de una factura borrador, su posterior duplicación programática
        para generar múltiples borradores, y finalmente, la validación masiva de estos documentos.
        """

        # Paso 1: Creación de la Factura Borrador (Simulación 00:07 - 00:15)
        move_line_vals = [
            (0, 0, {"product_id": self.producto.id, "quantity": 1.0, "price_unit": 100.00, "name": "Línea de Servicio"})
        ]

        factura_base = self.env["account.move"].create(
            {
                "partner_id": self.cliente.id,
                "move_type": "out_invoice",
                "invoice_date": date.today(),
                "invoice_line_ids": move_line_vals,
            }
        )

        # Validaciones de Estado Inicial (Post-Creación)
        self.assertEqual(factura_base.state, "draft", "La factura base debe estar en estado Borrador.")

        # Validaciones de Datos de Monto (Pre-Validación)
        self.assertAlmostEqual(
            factura_base.amount_untaxed, 100.00, msg="El subtotal (Excluido de Impuestos) debe ser $100.00."
        )
        self.assertAlmostEqual(
            factura_base.amount_total,
            100.00,
            msg="El total de la factura debe ser $100.00 (asumiendo 0% de impuesto para el test).",
        )
        self.assertAlmostEqual(factura_base.amount_tax, 0.00, msg="El impuesto de la factura debe ser $0.00.")

        # Paso 2: Duplicación de la Factura (Simulación 00:18 - 00:26)
        factura_duplicada_1 = factura_base.copy()
        factura_duplicada_2 = factura_base.copy()
        factura_duplicada_3 = factura_base.copy()
        facturas_duplicadas = factura_duplicada_1 + factura_duplicada_2 + factura_duplicada_3

        # Validaciones de Estado para Facturas Duplicadas
        self.assertTrue(
            all(f.state == "draft" for f in facturas_duplicadas),
            "Todas las facturas duplicadas deben estar en estado Borrador.",
        )

        # Paso 3: Validación Masiva (Simulación 00:33 - 00:40)
        facturas_a_validar = factura_base + facturas_duplicadas
        facturas_a_validar.action_post()

        # Validaciones de Estado Final (Post-Validación Masiva)
        self.assertTrue(
            all(f.state == "posted" for f in facturas_a_validar),
            "Todas las facturas deben haber pasado a estado Publicado/Validado ('posted').",
        )

        # Validaciones de Datos de Monto (Post-Validación)
        self.assertTrue(
            all(abs(f.amount_total - 100.00) < 0.001 for f in facturas_a_validar),
            "El total en todas las facturas validadas debe ser $100.00.",
        )

        # Validaciones de Relaciones y Documentos Generados
        self.assertTrue(
            all(f.line_ids for f in facturas_a_validar),
            "Cada factura validada debe tener líneas de asiento contable asociadas.",
        )
        self.assertTrue(
            all(f.state == "posted" for f in facturas_a_validar),
            "El estado 'posted' de las facturas implica la creación y contabilización del asiento contable subyacente.",
        )
        self.assertTrue(
            all(f.name != "Draft" for f in facturas_a_validar),
            "Cada factura validada debe tener un número de documento asignado (no 'Draft').",
        )
