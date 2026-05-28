##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
##############################################################################

import logging

from . import models

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Migrate from hash system to lock_posted_moves (compatible with v19)."""
    cr = env.cr

    # Check whether the source column exists (absent in fresh v19 installs)
    cr.execute(
        "SELECT 1 FROM information_schema.columns"
        " WHERE table_name = 'account_move' AND column_name = 'inalterable_hash'"
    )
    if cr.fetchone():
        # Check idempotency: backup already present means migration already ran
        cr.execute(
            "SELECT 1 FROM information_schema.columns"
            " WHERE table_name = 'account_move' AND column_name = 'x_bkp_inalterable_hash'"
        )
        if not cr.fetchone():
            # RENAME COLUMN + ADD COLUMN are O(1) catalog operations — no row scan.
            # Avoids a full-table UPDATE that causes install timeouts on large databases.
            cr.execute("ALTER TABLE account_move RENAME COLUMN inalterable_hash TO x_bkp_inalterable_hash")
            cr.execute("ALTER TABLE account_move ADD COLUMN inalterable_hash VARCHAR")
            _logger.info("account_lock_posted_moves: renamed inalterable_hash → x_bkp_inalterable_hash (no row scan)")
        else:
            # Backup column already exists: copy remaining non-null hashes and clear the source.
            cr.execute("""
                UPDATE account_move
                   SET x_bkp_inalterable_hash = inalterable_hash,
                       inalterable_hash = NULL
                 WHERE inalterable_hash IS NOT NULL
            """)
            _logger.info(
                "account_lock_posted_moves: cleaned inalterable_hash (%s records, backup preserved in x_bkp_inalterable_hash)",
                cr.rowcount,
            )
    else:
        _logger.info("account_lock_posted_moves: inalterable_hash column not present, nothing to migrate")

    cr.execute("""
        UPDATE account_journal
           SET lock_posted_moves = TRUE,
               restrict_mode_hash_table = FALSE
         WHERE restrict_mode_hash_table = TRUE
    """)
    _logger.info("account_lock_posted_moves: deprecated %s journals", cr.rowcount)
