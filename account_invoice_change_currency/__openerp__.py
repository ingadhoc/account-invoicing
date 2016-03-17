# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015  ADHOC SA  (http://www.adhoc.com.ar)
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'author': 'ADHOC SA',
    'category': 'Accounting & Finance',
    'demo_xml': [],
    'depends': ['account'],
    'description': '''
Account Invoice Change Currency
===============================
Replace original odoo wizard for changing currency on an invoice with serveral
improovements:

* Preview and allow to change the rate thats is going to be used:
* Log the currency change on the chatter
* Add this functionality to supplier invoices
''',
    'installable': True,
    'name': 'Account Invoice Change Currency',
    'test': [],
    'data': [
        'views/invoice_view.xml',
        'wizard/account_change_currency_view.xml',
    ],
    'version': '8.0.0.0.0',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3'}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
