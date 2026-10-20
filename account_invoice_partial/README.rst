.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

========================
Account Invoice Partial
========================

This module adds an **Invoice Percentage** button to draft customer invoices and credit notes. A wizard scales the quantity of every invoice line by a percentage, so the invoice can be issued for only a part of the original amount.

Features
========

**Percentage Wizard**
   Asks for the percentage to invoice, the rounding precision (``0.01`` by default) and the rounding method (``UP``, ``DOWN`` or ``HALF-UP``, ``HALF-UP`` by default).

**Quantities on Every Line**
   The quantity of each invoice line is multiplied by the percentage and rounded with the chosen precision and method. Prices are not changed, so totals and taxes follow the new quantities.

**Chatter Log**
   The invoice chatter records the percentage applied and the total before and after the change.

Installation
============

To install this module, you need to:

#. Install the ``account`` module (automatically handled as a dependency)
#. Install this module from the Apps menu or module list

Usage
=====

**Invoicing a Percentage**
   #. Go to **Accounting** ‣ **Customers** ‣ **Invoices** (or **Credit Notes**)
   #. Open a customer invoice or credit note in draft
   #. Click on the **Invoice Percentage** button
   #. Enter the percentage, the rounding precision and the rounding method
   #. Click **Confirm**: the quantity of every line is updated and the change is logged in the chatter

The button is only shown while the document is in draft. Running the wizard requires the ``account.group_account_invoice`` group.

Technical Details
=================

**New Models**
   * ``account.invoice.partial.wizard``: transient wizard that applies the percentage to the lines of the invoice

**Views**
   * ``account.move`` form: adds the **Invoice Percentage** button to the header, next to the post buttons

**Extension Point**
   * ``_get_partial_line_vals``: values written on each line, so other modules can apply the percentage to another field

**Security**
   * Access to the wizard is granted to ``account.group_account_invoice``

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
