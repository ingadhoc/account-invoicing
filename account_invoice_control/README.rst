.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=======================
Account Invoice Control
=======================

Restrict editing of customer invoices that come from sales orders.

Users that belong to the "Restrict Edit Invoice" group cannot edit the main
fields of a customer invoice (such as its lines, sales team, partner,
salesperson, due date and payment terms) when at least one of its lines is
linked to a sales order line, even if the invoice is still in draft.


Installation
============

To install this module, you need to:

#. Just install this module.


Configuration
=============

To configure this module, you need to:

#. Go to Settings -> Users & Companies -> Groups
#. Add the users you want to restrict to the "Restrict Edit Invoice" group


Usage
=====

To use this module, you need to:

#. Log in as a user of the "Restrict Edit Invoice" group
#. Go to Invoicing -> Customers -> Invoices
#. Open an invoice that has lines linked to a sales order: its main fields are read-only
#. Invoices without lines linked to a sales order are editable as usual in draft

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
