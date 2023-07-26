from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    # recalculate amount_currency for validated invoices and with another currency
    for line in env['account.move.line'].search(
        [('move_id.move_currency_id', '!=', False),
         ('account_id.user_type_id.type', 'in', ('receivable', 'payable')),
         ('currency_id', '=', False)]):
        amount = line.debit if line.debit else line.credit
        sign = 1.0 if line.debit else -1.0
        line._write({
            'currency_id': line.move_id.move_currency_id.id,
            'amount_currency': sign * line.move_id.move_currency_id.round(
                amount / line.move_id.move_inverse_currency_rate)})
