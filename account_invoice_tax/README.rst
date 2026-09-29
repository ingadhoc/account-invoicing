.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===================
Account Invoice Tax
===================

This module adds a wizard to vendor bills and vendor refunds to add or remove taxes on all invoice lines at once, and to set the tax amounts by hand.

Key Features
============

* **Add/update link on vendor bills**: draft vendor bills, refunds and receipts show an "Add/update" link next to the tax totals. The wizard only runs on vendor bills and vendor refunds; on any other document it raises an error.
* **Wizard with the current tax lines**: the wizard opens with one line per tax line of the entry and its amount in the invoice currency. Amounts on vendor refunds are shown with the sign of a vendor bill.
* **Add a tax to all lines**: a new purchase tax added in the wizard is linked to every product line. A tax that is already on some product line is not linked again to the other lines. New fixed taxes left with amount 0 are discarded.
* **Remove a tax from all lines**: a tax removed from the wizard is unlinked from every product line.
* **Manual amounts on fixed taxes**: the amount set for a fixed tax is written on its tax line and stored on the bill, so it survives later changes (price, quantity, new lines) until the bill is posted. Setting a fixed tax to 0 keeps it on the product lines with a zero amount.
* **Manual amounts on percentage taxes**: the amount is written on the tax line once; it is not stored, so the next recomputation of the taxes replaces it.
* **Fixed tax lines that net to zero are kept**: on vendor bills, a fixed tax whose lines cancel each other (a positive and a negative line) keeps its tax line when the tax has an amount or a manual amount, so the manual amount is not lost.
* **Tax totals show the manual amounts**: the totals widget shows the manual amounts of fixed taxes, also for tax groups shown in their own subtotal ("Preceding Subtotal"), and the following subtotals include them.
* **Read-only tax amounts in the totals widget**: the inline edition of tax amounts in the totals widget is replaced by a read-only amount, on every journal entry.
* **Foreign currency**: amounts are entered in the invoice currency and converted with the invoice currency rate.
* **Rate change and deleted line**: when the invoice currency rate changes at the same time as a taxed line is deleted, the tax lines are recomputed from the remaining lines.
* **Analytic taxes are not allowed**: the wizard raises an error if a tax has "Include in Analytic Cost" set.

Installation
============

To install this module, simply add it to your Odoo addons path and install it from the Apps menu.

Configuration
=============

No additional configuration is required.

Usage
=====

1. Open a vendor bill or vendor refund in draft state.
2. Click "Add/update" next to the tax totals.
3. In the wizard, add a tax line, remove a tax line, or change the amount of a tax.
4. Click "Update" to apply the changes to the invoice lines and the journal entry.

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
