{
    'name': 'Account Background Post',
    'version': "17.0.1.0.0",
    'author': 'ADHOC SA',
    'depends': [
        'account',
    ],
    'data': [
        'views/account_move_views.xml',
        'wizards/validate_account_move_views.xml',
        'data/ir_cron.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
