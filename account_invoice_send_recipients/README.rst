.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===============================
Account Invoice Send Recipients
===============================

* Adds a "Receive Invoices by Email" flag on contacts, available both on the main contact form and on the subcontact popup (any contact type).
* When sending a customer invoice or refund, automatically adds the customer contacts flagged with that field (and with an email) as recipients, on top of the default ones.
* Captures the whole contact hierarchy of the customer (sub-subcontacts included) via ``commercial_partner_id``, regardless of nesting or contact type.
* Covers the three sending paths with a single extension point: individual send, batch send and automatic (cron) send.
* Non-intrusive: recipients are pre-loaded but the field stays editable, so the user can remove them before sending.
* Scope: customer invoices and credit notes (``out_invoice`` / ``out_refund``).

Installation
============

To install this module, you need to:

#. Only need to install the module

Configuration
=============

To configure this module, you need to:

#. Go to the customer contact (or any of its subcontacts) and enable "Receive Invoices by Email"

Usage
=====

To use this module, you need to:

#. Create and confirm a customer invoice (or credit note) for that customer
#. Send the invoice by email: the flagged contacts are pre-loaded as recipients along with the default one
#. If needed, remove any recipient before sending

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
