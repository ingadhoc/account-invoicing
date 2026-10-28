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

This module adds a website category to commission rules, so a rule can apply only to the products of that website category or of any of its subcategories, whether they are published or not. It is installed automatically when both **Account Invoice Commission** and **eCommerce** are installed.

Features
========

* Filter commission rules by website (public) category
* A rule on a category also applies to the products of its subcategories
* Rules without website category keep applying to every product
* Invoice lines without product only take rules without website category

Installation
============

To install this module, follow these steps:

1. Go to **Apps** in Odoo
2. Search for **Commission Invoices with Public Categories**
3. Click **Install**

The module is installed automatically when ``account_invoice_commission`` and ``website_sale`` are installed.

Configuration
=============

To configure commission rules by website category:

#. Go to **Accounting > Configuration > Invoicing > Commission Rules**
#. Create or edit a commission rule
#. Set **Website Category** to make the rule apply only to products of that category or its subcategories

Usage
=====

When the commission of an invoice line is computed, the rule must also match the website category of the line product:

* A rule without **Website Category** applies to any product
* A rule with **Website Category** applies when one of the website categories of the product is that category or one of its subcategories
* A line without product only takes rules without **Website Category**

Among the rules that match, the first one by sequence is used, as in ``account_invoice_commission``.

Technical Details
=================

This module adds the following field to commission rules (``account.commission.rule``):

* **Website Category** (``public_category_id``): Many2one to ``product.public.category``

It extends ``_get_rule_domain`` to add the website category condition, using ``parent_of`` over the website categories of the product (``public_categ_ids``), and adds the field to the commission rules list view (``account_invoice_commission.account_commission_rule_tree``).

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
