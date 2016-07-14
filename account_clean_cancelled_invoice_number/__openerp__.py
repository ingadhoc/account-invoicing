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
    'name': 'Clean Cancelled Invoice Number',
    'version': '9.0.1.0.0',
    'category': 'Accounting',
    'sequence': 14,
    'summary': 'Invoicing, Number, Cancelled',
    'description': """
Clean Cancelled Invoice Number
========================
Adds a button on invoice to allow clean number to cancelled invoices in order to:
* Regenerate the invoice number with new sequence number
* Delete the invoice
    """,
    'author':  'ADHOC SA',
    'website': 'www.adhoc.com.ar',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'account_cancel'
    ],
    'data': [
        'account_invoice_view.xml',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': False,
    'auto_install': False,
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: