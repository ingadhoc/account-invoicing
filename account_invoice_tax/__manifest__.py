{
    "name": "Account Invoice Tax",
<<<<<<< f61fb73cd792094d6ae12983f3a38120ca97c639
    "version": "19.0.1.1.2",
||||||| 8a6a5811224f58751dfd9dfb5c1ffef5d9bff6d0
    "version": "18.0.1.2.0",
=======
    "version": "18.0.1.2.1",
>>>>>>> ff013750f202fcd1efb74fd7cda4302821c1df59
    "author": "ADHOC SA",
    "category": "Localization",
    "depends": [
        "account",
    ],
    "data": [
        "wizards/account_invoice_tax_view.xml",
        "views/account_move_view.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "account_invoice_tax/static/src/xml/**/*",
        ],
    },
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
