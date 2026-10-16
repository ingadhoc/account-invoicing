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

- Allows to set Rules Commission.

- Creates a tab in Commission Invoices (supplier invoice) that allows users to add Commisioned Invoices (customer invoice) based on settled rules commission.

- Creates a tab in Commissioned Invoices that shows the applied Commision Invoices.

- Adds a Last Payment Date on invoices, computed from the reconciled payments and available in the invoice search view.


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

#. Go to Invoicing > Configuration > Invoicing > Commission Rules and create
   the rules. The menu needs the Billing Administrator access right. A rule
   can be limited by validity dates, a minimum amount (checked against the
   invoice line), agent, customer, product template, product category and
   account, and it sets the commission percentage. The first rule that
   matches, by sequence, is the one applied.

#. Open the commission invoice (a vendor bill for the agent) and go to the
   Commission tab. Add there the customer invoices being commissioned: the
   Commission Amount column shows what each one pays according to the rules.

#. On a customer invoice, the Commissions tab shows the commission invoices
   that commission it.

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
