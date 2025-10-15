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

This module provides a wizard to create partial invoices from existing customer invoices in Odoo. It allows users to generate new invoices with partial quantities or amounts from the original invoice lines.

Features
========

**Partial Invoice Creation Wizard**
   Create new invoices with partial quantities from existing customer invoices through an intuitive wizard interface.

**Line-by-Line Control**
   Select specific invoice lines and define partial quantities for each line item independently.

**Automatic Invoice Generation**
   Generate properly formatted partial invoices that maintain proper accounting relationships and traceability.

Installation
============

To install this module, you need to:

#. Install the ``account`` module (automatically handled as a dependency)
#. Install this module from the Apps menu or module list

Usage
=====

**Creating Partial Invoices**
   #. Go to **Accounting** ‣ **Customers** ‣ **Invoices**
   #. Open an existing customer invoice
   #. Click on the "Create Partial Invoice" action button
   #. In the wizard, select the invoice lines you want to include
   #. Specify the partial quantities for each selected line
   #. Click "Create Partial Invoice" to generate the new invoice

**Managing Partial Invoice Lines**
   #. The wizard displays all available invoice lines from the source invoice
   #. Enter the desired quantity for each line (must be less than or equal to the original quantity)
   #. Only lines with quantities greater than zero will be included in the new partial invoice

Technical Details
=================

**Models Extended**
   * ``account.move``: Enhanced with partial invoice creation capabilities

**New Models**
   * ``account.invoice.partial.wizard``: Main wizard for partial invoice creation
   * ``account.invoice.partial.wizard.line``: Individual line items in the partial invoice wizard

**Security**
   * Proper access controls defined for the wizard models
   * Inherits standard invoice security permissions

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
