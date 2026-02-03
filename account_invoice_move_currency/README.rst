.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==============================
Account Invoice Move Currency
==============================

This module adds an editable field for the user to report the exchange rate on customer invoices.

The module provides:

* A secondary currency field for informative purposes on invoices
* An informative exchange rate field that displays the rate between the secondary currency and the company currency
* These fields are automatically calculated but can be edited when the invoice is in draft state

The informative exchange rate helps users understand currency conversions at the time of the invoice without affecting the accounting entries.

Installation
============

To install this module, you need to:

#. Install the module dependencies
#. Install this module from Apps menu

Configuration
=============

To configure this module, you need to:

#. No specific configuration needed
#. Make sure you have the proper exchange rates configured in your system

Usage
=====

To use this module, you need to:

#. Go to Accounting > Customers > Invoices (or Vendor Bills)
#. Create or edit an invoice/bill in draft state
#. When the invoice currency is different from the company currency, you will see:

   * **Rate Currency**: Select a secondary currency for reference
   * **Informative Exchange Rate**: Shows the exchange rate (automatically calculated, but editable in draft)

#. The fields are visible only when:

   * The invoice currency differs from the company currency
   * The move type is invoice or refund (customer/vendor)

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

* ADHOC SA: `Icon <https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png>`__.

Contributors
------------

Maintainer
----------

.. image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

This module is maintained by the ADHOC SA.

To contribute to this module, please visit https://www.adhoc.com.ar.
