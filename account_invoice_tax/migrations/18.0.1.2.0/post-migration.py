import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Populate tax_override_data for vendor bills that have fixed-amount tax
    lines but whose override data was never stored.

    Targets invoices of type in_invoice / in_refund / in_receipt created in
    the last month that:
      - have at least one tax line linked to a fixed-amount tax, and
      - have tax_override_data IS NULL (never set).

    Processes up to BATCH_LIMIT records.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    month_start = date.today() - relativedelta(months=3)

    moves = env["account.move"].search(
        [
            ("move_type", "in", ["in_invoice", "in_refund", "in_receipt"]),
            ("invoice_date", ">=", month_start),
            ("tax_override_data", "=", False),
            ("line_ids.tax_line_id.amount_type", "=", "fixed"),
        ],
        limit=1000,
        order="id desc",
    )

    if not moves:
        _logger.info("account_invoice_tax migration: no invoices to process.")
        return

    _logger.info("account_invoice_tax migration: processing %d invoice(s).", len(moves))
    moves.sync_tax_override_from_tax_totals()

    _logger.info("account_invoice_tax migration: done.")
