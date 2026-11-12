.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=======================
Account Background Post
=======================

This module let the user to improve the use of the post entries action on the invoices list view.

1. Let the user to post the entries in Background. This new option on the wizard will mark the invoices to be validated so they can be validated in Background, if we found and error with one of them, we leave a message in the invoice notifying the internal users and unmark the invoice so the validate process can continue with other invoices.

   1.1 The marked invoices can also carry a scheduling date ("Post in Background At", ``background_post_date``). The cron only posts them once that date is reached, so a caller can defer a posting to a known future moment (for example, the next invoice date of a subscription) instead of posting on the next run. Without a date the behaviour is the historical one: the invoice is posted on the next cron run.

   1.2 Optionally, an invoice that fails can be retried instead of being unmarked on the first error. While there are retries left we reschedule the invoice (and count the attempt on ``background_post_attempts``); once they are exhausted we unmark it and leave the message in the invoice, as always. Retries are disabled by default, so the behaviour does not change unless they are configured.

2. If the user want to validate the invoices at the current moment not in Background, we do the next two changes:

   2.1 We only let the user to validate small batch of invoices. By default only 20 invoices. If the user try to select more than 20 invoices then we force him to use Post in Background option.

   2.2 If they select less than 20 then we let them validate the invoices but we validate each one by one, formerly this method was trying to validate all the invoices at once and if there was some error on one of the invoices then we fail all the info of the correctly validated ones.

   IMPORTANT: Batch size by default is 20, but if the user want to use another size they can define a system parameter with name "account_background_post.batch_size" to force a different batch size.

Installation
============

To install this module, you need to:

#. Only need to install the module

Configuration
=============

To configure this module, you need to:

#. Nothing to configure, but the following system parameters are available:

   * ``account_background_post.batch_size`` (default 20): how many invoices the user can validate synchronously before being forced to use the background option.
   * ``account_background_post.max_retries`` (default 0): how many times the cron retries an invoice that failed before unmarking it and notifying the error. With 0 there are no retries.
   * ``account_background_post.retry_delay_minutes`` (default 30): how long to wait before retrying an invoice that failed.

Usage
=====

To use this module, you need to:

#. Go the invoices list view and select a batch of invoices.
#. Go to action menu and click on post entries option.
#. Use Post in Background or Post Journal Entries depending of what they need to know.

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
