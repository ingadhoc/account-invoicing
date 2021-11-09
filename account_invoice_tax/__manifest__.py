{
    'name': 'Account Invoice Tax',
    'version': "13.0.1.1.0",
    'author': 'ADHOC SA',
    'category': 'Localization',
    'depends': [
        'account',
        'account_ux',  # for _recompute_tax_lines patch
    ],
    'data': [
        'wizards/account_invoice_tax_view.xml',
        'views/account_move_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
