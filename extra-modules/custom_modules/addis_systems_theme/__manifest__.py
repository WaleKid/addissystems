{
    "name": "Addis Systems Theme",
    "version": "16.0.1.0",
    "sequence": 1,
    "summary": "Addis Systems Theme",
    "description": """
        This is a Theme for Addis Systems Instances.
            ========================================
    """,
    "category": "Addis Systems/Themes",
    "author": "Addis Systems/Beruk W.",
    "website": "https://www.addissystems.et/",
    "license": "LGPL-3",
    "depends": ["base", "web", "web_editor"],
    "external_dependencies": {},
    "data": [
        "templates/webclient.xml",
        "views/AddisSystemsLoginPageView.xml",
        "reports/AddisSystemReportLayout.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            (
                "after",
                "web/static/src/scss/primary_variables.scss",
                "addis_systems_theme/static/src/colors.scss",
            )
        ],
        "web._assets_backend_helpers": [
            "addis_systems_theme/static/src/variables.scss",
            "addis_systems_theme/static/src/mixins.scss",
        ],
        "web.assets_backend": [
            "addis_systems_base/static/src/webclient/user_menu/user_menu_items.js",
            "addis_systems_theme/static/src/js/tax_totals.js",
            "addis_systems_theme/static/src/js/web_window_title.js",
            "addis_systems_theme/static/src/xml/tax_totals.xml",
            "addis_systems_theme/static/src/base/**/*.xml",
            "addis_systems_theme/static/src/base/**/*.scss",
            "addis_systems_theme/static/src/base/**/*.js",
            "addis_systems_theme/static/src/webclient/**/*.xml",
            "addis_systems_theme/static/src/webclient/**/*.scss",
            "addis_systems_theme/static/src/webclient/**/*.js",
            "addis_systems_theme/static/src/views/**/*.scss",
        ],
        "web.assets_frontend": [],
        "web.assets_tests": [],
        "web.qunit_suite_tests": [],
        "web.assets_qweb": [],
    },
    "demo": [],
    "post_init_hook": "_post_init_hook",
    "uninstall_hook": "_uninstall_cleanup",
    "installable": True,
    "price": 50.00,
    "currency": "ETB",
    "application": True,
    "auto_install": True,
}
