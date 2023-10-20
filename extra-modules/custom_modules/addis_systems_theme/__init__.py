from odoo import api, SUPERUSER_ID
from . import models, controllers


def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    spreadsheet_dashboard = (env["ir.module.module"].sudo().search([("name", "=", "spreadsheet_dashboard")]))
    spreadsheet_dashboard.button_install()
    discuss = env["ir.module.module"].sudo().search([("name", "=", "mail")])
    discuss.button_install()
    web_editor = env["ir.module.module"].sudo().search([("name", "=", "web_editor")])
    web_editor.button_install()
    inventory = env["ir.module.module"].sudo().search([("name", "=", "stock")])
    inventory.button_install()
    sales = env["ir.module.module"].sudo().search([("name", "=", "sale_management")])
    sales.button_install()
    purchase = env["ir.module.module"].sudo().search([("name", "=", "purchase")])
    purchase.button_install()
    ethiopia_account = env["ir.module.module"].sudo().search([("name", "=", "l10n_et")])
    ethiopia_account.button_install()
    accounting = env["ir.module.module"].sudo().search([("name", "=", "om_account_accountant")])
    accounting.button_install()


def _uninstall_cleanup(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["web_editor.assets"].reset_asset("/addis_systems_theme/static/src/colors.scss", "web._assets_primary_variables")
