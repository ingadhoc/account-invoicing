{
    "name": "Latam Invoice Document UX",
    "version": "19.0.1.2.0",
    "author": "ADHOC SA",
    "website": "www.adhoc.com.ar",
    "license": "AGPL-3",
    "category": "Localization",
    "depends": [
        "l10n_latam_invoice_document",
    ],
    "data": [
        "views/account_move_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "l10n_latam_invoice_document_ux/static/src/js/account_move_form.js",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
