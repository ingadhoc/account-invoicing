import logging

from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID, api, fields

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Limpia la falsa marca de salto de secuencia (`made_sequence_gap`) en comprobantes cuyo diario
    usa documentos, de los últimos 2 meses.

    En v19 el cálculo del flag pasó a `_update_sequence_made_gap`, pero la exclusión que
    `l10n_latam_invoice_document` aplicaba a los comprobantes con documentos no se trasladó al
    método nuevo, así que volvieron a marcarse en rojo. El override (ver models/account_move.py)
    lo corrige de acá en adelante; esta migración limpia las ya almacenadas.

    Re-ejecutable: solo toca registros que todavía tengan `made_sequence_gap = True`.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    cutoff = fields.Date.today() - relativedelta(months=2)
    moves = env["account.move"].search(
        [
            ("l10n_latam_use_documents", "=", True),
            ("made_sequence_gap", "=", True),
            ("invoice_date", ">=", cutoff),
        ]
    )
    if moves:
        moves.made_sequence_gap = False
        _logger.info(
            "l10n_latam_invoice_document_ux: limpiada la falsa marca made_sequence_gap en %s comprobantes desde %s",
            len(moves),
            cutoff,
        )
