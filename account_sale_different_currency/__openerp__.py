# -*- coding: utf-8 -*-
{
    'name': 'Invoice in different Currency than Sale Order',
    'version': '8.0.0.5.1',
    'category': 'Account',
    'description': """
Invoice in different Currency than Sale Order
=============================================
Modulo para cubrir la siguiente necesidad:
------------------------------------------
* Generar presupuestos en dolares
* Generar facturas de adelantos en pesos pero que ‘descuenten’ al presupuesto en dolares
* Generar factura final en pesos descontando todos los adelantos

Ejemplo de uso:
---------------
* Orden de venta - USD - OV001
    * Servicio 1 --> 1 x 1000
    * Servicio 2 --> 1 x 5000
* Factura 1 - ARS (cotización 10) - 0001-00000001
    * Adelanto OV001 (Servicio 1, Servicio 2) --> $10000 (almacenando el equivalente a USD 1000)
* Factura 2 - ARS (cotización 11) - 0001-00000002
    * Adelanto OV001 (Servicio 1, Servicio 2) --> $11000 (almacenando el equivalente a USD 1000)
* Factura 3 - ARS (saldo, cotización 12)
    * Servicio 1 --> 1 x 12000
    * Servicio 2 --> 1 x 60000
    * Adelanto 0001-00000001 --> 1 x - 10000
    * Adelanto 0001-00000002 --> 1 x - 11000
    * Ajuste x diferencia cambiaria --> 1 x -3000
    * TOTAL = $48000

Errores en redondeo:
--------------------
Si se tienen errores en reondeo es recomendable ajustar la precision de las
monedas pertinentes y de "account" y "product" a 3 decimales.
    """,
    'author': 'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'depends': [
        'sale',
        'account_analytic_analysis'
    ],
    'data': [
        'wizard/sale_make_invoice_advance.xml',
        'invoice_view.xml',
        'pricelist_view.xml',
        'sale_view.xml',
        'company_view.xml',
        'account_analytic_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
