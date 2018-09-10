.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===================
Commission Invoices
===================

Simple module that links a commission invoice (supplier invoice) to the commissioned invoices (customer invoices)

TODO
====

Para mejora de performance, cuando se buscan facturas a agregar, no deberiamos mandar en el contexto el "commissioned_partner_id" así no calcula hasta que se agregaron las facturas.

Some other similar modules and some ideas:
    * agregar campo "commission" en lineas de factura y factura que se calcule en función a otros campos a
    * agregar en productos y partners para definir las comisiones
    * el campo commission de facturas no debería re calcularse
    * también debería setarse si se paga comisiones sobre valores netos o no (o tal vez no lo hacemos opción y listo, que vaya sobre neto).
    * Y tal vez puede ser parametro si debe estar pagada o no (así calculamos el campo en ese momento o no)
    * alguna clase padre para gestionar y disparar todas las comisiones? Desde usuarios? desde partners? También podría servir para re-calcular ya que no serían campos calculados
    * https://github.com/OCA/commission/blob/9.0/sale_commission
    * https://www.odoo.com/apps/modules/10.0/sales_commission_multi_level/
    * https://www.odoo.com/apps/modules/10.0/sales_commission_calculation/
    * https://www.odoo.com/apps/modules/10.0/sale_commission_gt/
    * https://www.odoo.com/apps/modules/10.0/sales_commission_generic/
    * https://www.odoo.com/apps/modules/10.0/sales_commission_external_user/
    * https://www.odoo.com/apps/modules/10.0/aspl_sales_commission/
    * https://github.com/Vauxoo/addons-vauxoo/blob/9.0/commission_payment/
    * https://github.com/Vauxoo/addons-vauxoo/blob/9.0/hr_salesman_commission
    * https://github.com/Vauxoo/addons-vauxoo/tree/9.0/invoice_commission


Installation
============

To install this module, you need to:

#. Just install this module.


Configuration
=============

To configure this module, you need to:

#. No configuration nedeed.


Usage
=====

To use this module, you need to:

#. Go to ...

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: http://runbot.adhoc.com.ar/

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/ingadhoc/account-invoicing/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* |company| |icon|

Contributors
------------

Maintainer
----------

|company_logo|

This module is maintained by the |company|.

To contribute to this module, please visit https://www.adhoc.com.ar.
