{
    "name": "Account Invoice Tax",
<<<<<<< 24dad28271a7be0f910c94eae5e492a680c86b6a
    "version": "19.0.1.0.0",
||||||| fa5caa84911bca5b06138eb1bc5dc3d52a23458c
    "version": "18.0.1.0.0",
=======
    "version": "18.0.1.2.0",
>>>>>>> 9d1cd66e35c3227decb6be584534c1605bd1c831
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
