##############################################################################
#
#    Copyright (C) 2026  ADHOC SA  (http://www.adhoc.com.ar)
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
    "name": "Account Lock Posted Moves",
    "author": "ADHOC SA",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Flexible lock system for posted entries (replaces hash locking)",
    "depends": [
        "account",
    ],
    "data": [
        "views/account_journal_views.xml",
    ],
    "website": "www.adhoc.com.ar",
    "installable": True,
    "post_init_hook": "post_init_hook",
}
