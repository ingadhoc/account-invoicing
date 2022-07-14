# import base64
# import time
# from odoo.tests import common
from odoo.tests.common import Form
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestNumberInvoice(AccountTestInvoicingCommon):

    def _test_1_invoices(self):
        import pdb; pdb.set_trace()
        payment_term_id = self.env.ref("account.account_payment_term_end_following_month")
        invoice_user_id = self.env.user
        invoices_to_create = {
            'test_invoice_1': {
                "ref": "test_invoice_1: Invoice to gritti support service, vat 21",
                "partner_id": self.res_partner_gritti_mono,
                "invoice_user_id": invoice_user_id,
                "invoice_payment_term_id": payment_term_id,
                "move_type": "out_invoice",
                "invoice_date": "2021-03-01",
                "company_id": self.company_ri,
                "invoice_line_ids": [
                    {'product_id': self.service_iva_21}
                ],
            },
        }

        with Form(self.env['account.move'].with_context(default_move_type=values['move_type'])) as invoice_form:
            invoice_form.ref = values['ref']
            invoice_form.partner_id = values['partner_id']
            invoice_form.invoice_user_id = values['invoice_user_id']
            invoice_form.invoice_payment_term_id = values['invoice_payment_term_id']
            if not use_current_date:
                invoice_form.invoice_date = values['invoice_date']
            if values.get('invoice_incoterm_id'):
                invoice_form.invoice_incoterm_id = values['invoice_incoterm_id']
            for line in values['invoice_line_ids']:
                with invoice_form.invoice_line_ids.new() as line_form:
                    line_form.product_id = line.get('product_id')
                    line_form.price_unit = line.get('price_unit')
                    line_form.quantity = line.get('quantity')
                    if line.get('tax_ids'):
                        line_form.tax_ids = line.get('tax_ids')
                    line_form.name = 'xxxx'
                    line_form.account_id = self.company_data['default_account_revenue']
        invoice = invoice_form.save()
        self.assertEqual(invoice.invoice_line_ids[0].number, 1)
    # @classmethod
    # def setUpClass(cls, chart_template_ref=None):
    #     super().setUpClass(chart_template_ref=chart_template_ref)
    # @classmethod
    # def setUpClass(cls, chart_template_ref=None):
    #     import pdb; pdb.set_trace()
    #     super().setUpClass(chart_template_ref=chart_template_ref)
        # cls.company_data['company'].write({
        #     'parent_id': cls.env.ref('base.main_company').id,
        #     'currency_id': cls.env.ref('base.ARS').id,
        #     'name': '(AR) Responsable Inscripto (Unit Tests)',
        #     "l10n_ar_afip_start_date": time.strftime('%Y-01-01'),
        #     'l10n_ar_gross_income_type': 'local',
        #     'l10n_ar_gross_income_number': '901-21885123',
        # })
        # cls.company_ri = cls.company_data['company']

        # cls.company_ri.partner_id.write({
        #     'name': '(AR) Responsable Inscripto (Unit Tests)',
        #     'l10n_ar_afip_responsibility_type_id': cls.env.ref("l10n_ar.res_IVARI").id,
        #     'l10n_latam_identification_type_id': cls.env.ref("l10n_ar.it_cuit").id,
        #     'vat': '30111111118',
        #     "street": 'Calle Falsa 123',
        #     "city": 'Rosario',
        #     "country_id": cls.env.ref("base.ar").id,
        #     "state_id": cls.env.ref("base.state_ar_s").id,
        #     "zip": '2000',
        #     "phone": '+1 555 123 8069',
        #     "email": 'info@example.com',
        #     "website": 'www.example.com',
        # })
        # cls.partner_ri = cls.company_ri.partner_id

        # cls.res_partner_gritti_mono = cls.env['res.partner'].create({
        #     "name": "Gritti Agrimensura (Monotributo)",
        #     "is_company": 1,
        #     "city": "Rosario",
        #     "zip": "2000",
        #     "state_id": cls.env.ref("base.state_ar_s").id,
        #     "country_id": cls.env.ref("base.ar").id,
        #     "street": "Calle Falsa 123",
        #     "email": "info@example.com.ar",
        #     "phone": "(+54) (341) 111 2222",
        #     "website": "http://www.grittiagrimensura.com",
        #     'l10n_latam_identification_type_id': cls.env.ref("l10n_ar.it_cuit").id,
        #     'vat': "27320732811",
        #     'l10n_ar_afip_responsibility_type_id': cls.env.ref("l10n_ar.res_RM").id,
        # })

        # cls.service_iva_21 = cls.env['product.product'].create({
        #     # demo data product.product_product_2
        #     'name': 'Virtual Home Staging (VAT 21)',
        #     'uom_id': uom_hour.id,
        #     'uom_po_id': uom_hour.id,
        #     'list_price': 38.25,
        #     'standard_price': 45.5,
        #     'type': 'service',
        #     'default_code': 'VAT 21',
        #     'taxes_id': [(6, 0, cls.tax_21.ids)],
        # })

