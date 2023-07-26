from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    # recalculate debt for validated invoices and with another currency
    invoices = env['account.invoice'].search([
        ('state', '=', 'open'), ('move_currency_id', '!=', False)])
    for rec in invoices:
        rec._compute_residual()
