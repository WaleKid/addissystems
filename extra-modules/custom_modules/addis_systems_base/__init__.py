from odoo import api, SUPERUSER_ID
from . import models, wizards, controllers


def _pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    discuss = env['ir.module.module'].sudo().search([('name', '=', 'mail')])
    discuss.button_install()
    web_editor = env['ir.module.module'].sudo().search([('name', '=', 'web_editor')])
    web_editor.button_install()
    inventory = env['ir.module.module'].sudo().search([('name', '=', 'stock')])
    inventory.button_install()
    sales = env['ir.module.module'].sudo().search([('name', '=', 'sale_management')])
    sales.button_install()
    pos = env['ir.module.module'].sudo().search([('name', '=', 'point_of_sale')])
    pos.button_install()
    purchase = env['ir.module.module'].sudo().search([('name', '=', 'purchase')])
    purchase.button_install()


def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    print("---------------------------------------- post_load --------------------------------------------")
    print("2, Will be used for starting AS consumer listener when stable")
    print("------------------------------------------------------------------------------------------------")


def _post_load():
    print("---------------------------------------- post_load --------------------------------------------")
    print("1, Will be used for starting AS consumer listener when stable")
    print("------------------------------------------------------------------------------------------------")


def _uninstall_cleanup(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['web_editor.assets'].reset_asset('/addis_systems_base/static/src/colors.scss', 'web._assets_primary_variables')
