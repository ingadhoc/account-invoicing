from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    # recalculamos deuda para facturas cons aldo y other currency
    invoices = env['account.invoice'].search([
        ('reconciled', '=', False), ('move_currency_id', '!=', False)])
    invoices._compute_residual()
