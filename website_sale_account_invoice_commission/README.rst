.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=======================================
Website Sale Account Invoice Commission
=======================================

This module extends the commission functionality to work with website sales and invoices. It allows you to configure commission rules that apply to orders created through the website and ensures commissions are properly calculated based on invoice amounts.

Features
========

* Define commission rules that apply to website sales
* Configure whether to use the invoice total instead of the sale order total for commission calculation
* Automatic commission calculation based on actual invoiced amounts
* Seamless integration with Odoo's e-commerce and invoicing workflow

Installation
============

To install this module, follow these steps:

1. Go to **Apps** in Odoo
2. Search for **Website Sale Account Invoice Commission**
3. Click **Install**

Configuration
=============

To configure commission rules for website sales:

#. Go to **Accounting > Configuration > Commission Rules**
#. Create or edit a commission rule
#. Define **Website category** to make this rule applicable to website orders"
#. Optionally check **Use Invoice Total** to calculate commissions based on the invoice amount rather than the sale order amount

Usage
=====

Once configured, commissions will be automatically calculated for website orders:

* When a customer places an order through the website, eligible commission rules will apply
* If **Use Invoice Total** is enabled, the commission amount will be recalculated based on the actual invoice total (useful for partial invoicing or invoice adjustments)
* Commission amounts will respect the invoice currency and conversion rates

Technical Details
=================

This module adds the following fields to commission rules:

* **Website Sale** (``website_sale``): Many2one field to mark rules applicable to website orders
* **Use Invoice Total** (``use_invoice_total``): Boolean field to calculate commissions from invoice amounts instead of sale order amounts

The commission calculation considers:

* Invoice amounts in their original currency with proper conversion
* Only confirmed and posted invoices
* Tax-included or tax-excluded amounts based on rule configuration

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
