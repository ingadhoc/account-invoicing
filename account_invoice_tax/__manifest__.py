{
    'name': 'Account Invoice Tax',
    'version': "16.0.1.3.0",
    'author': 'ADHOC SA',
    'category': 'Localization',
    'depends': [
        'account',
    ],
    'data': [
        'wizards/account_invoice_tax_view.xml',
        'views/account_move_view.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'account_invoice_tax/static/src/xml/**/*',
        ],
    },
    'license': 'AGPL-3',
    'installable': False,
    'auto_install': False,
    'application': False,
}
