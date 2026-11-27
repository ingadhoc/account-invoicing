##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
##############################################################################
{
    "name": "Thermal Invoice Ticket for 80mm Printers",
    "version": "20.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Thermal invoice report for 80mm paper, localization independent",
    "author": "ADHOC SA",
    "website": "www.adhoc.com.ar",
    "license": "AGPL-3",
    "depends": [
        "account",
    ],
    "data": [
        "views/thermal_invoice_reports.xml",
        "views/thermal_invoice_templates.xml",
        "views/account_move_views.xml",
        "views/res_company_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_thermal_ticket/static/src/js/thermal_print.js",
        ],
        "web.report_assets_common": [
            "account_thermal_ticket/static/src/scss/thermal_invoice.scss",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
