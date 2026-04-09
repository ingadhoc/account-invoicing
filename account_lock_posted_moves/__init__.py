##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
##############################################################################

import logging

from . import models

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Migrate from hash system to lock_posted_moves (compatible with v19)."""
    cr = env.cr
    cr.execute("SELECT * FROM account_move WHERE inalterable_hash IS NOT NULL LIMIT 1")
    if cr.fetchone():
        # Create backup column if it doesn't exist
        cr.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = 'account_move' AND column_name = 'x_bkp_inalterable_hash'"
        )
        if not cr.fetchone():
            cr.execute("ALTER TABLE account_move ADD COLUMN x_bkp_inalterable_hash VARCHAR")

        # Copy hash values to backup (equivalent to openupgrade.copy_columns)
        cr.execute(
            "UPDATE account_move SET x_bkp_inalterable_hash = inalterable_hash WHERE inalterable_hash IS NOT NULL"
        )

        # Clean inalterable_hash
        cr.execute("UPDATE account_move SET inalterable_hash = NULL WHERE inalterable_hash IS NOT NULL")
        _logger.info(
            "account_lock_posted_moves: cleaned inalterable_hash (%s records, backup preserved in x_bkp_inalterable_hash)",
            cr.rowcount,
        )
    else:
        _logger.info("account_lock_posted_moves: no hash values found to backup")

    # Migrate lock_posted_moves values based on restrict_mode_hash_table
    cr.execute(
        "UPDATE account_journal SET lock_posted_moves = restrict_mode_hash_table WHERE restrict_mode_hash_table = TRUE"
    )

    cr.execute("UPDATE account_journal SET restrict_mode_hash_table = FALSE WHERE restrict_mode_hash_table = TRUE")
    _logger.info("account_lock_posted_moves: deprecated %s journals", cr.rowcount)
