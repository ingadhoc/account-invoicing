.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

Account Lock Posted Moves
==========================

This module replaces the deprecated hash-based locking system (``restrict_mode_hash_table``) with a simple, flexible lock system for posted accounting entries.

**Key Features:**

* **Simple Lock System**: New boolean field "Lock Posted Entries" on journals
* **Flexible**: Administrators can temporarily disable the lock to modify posted entries
* **Better Performance**: No SHA256 hash calculation required
* **Clean Migration**: Automatically cleans up ``inalterable_hash`` values on installation

Installation
============

During installation, the module automatically:

1. Creates a backup table (``account_move_hash_backup``) with existing hash values
2. Clears all ``inalterable_hash`` values from account moves
3. Disables the deprecated ``restrict_mode_hash_table`` field on all journals

The old ``restrict_mode_hash_table`` field will be hidden from the UI.

Configuration
=============

To enable entry locking on a journal:

#. Go to **Accounting > Configuration > Journals**
#. Open a journal (e.g., Customer Invoices)
#. Go to the **Advanced Settings** tab
#. In the **Entry Protection** section, enable **Lock Posted Entries**

Usage
=====

Protecting Posted Entries
--------------------------

Enable "Lock Posted Entries" on a journal to prevent users from resetting posted entries to draft.

Modifying Locked Entries
-------------------------

If you need to modify a posted entry in a locked journal:

#. Go to the journal configuration
#. Temporarily disable "Lock Posted Entries"
#. Reset the entry to draft and make your changes
#. Post the entry again
#. Re-enable "Lock Posted Entries"

The system will show a warning message when the lock is active.

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

This module is maintained by ADHOC SA.

To contribute to this module, please visit https://github.com/ingadhoc/account-invoicing.
