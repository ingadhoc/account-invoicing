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
    'name': 'Account Invoice Prices Update',
    'version': "15.0.1.0.0",
    'author': 'ADHOC SA',
    'license': 'AGPL-3',
    'category': 'Accounting & Finance',
    'website': 'www.adhoc.com.ar',
    'depends': [
        'account'
    ],
    'data': [
        'wizards/update_prices_wizard_views.xml',
        'views/account_move_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
