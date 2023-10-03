from odoo import api, SUPERUSER_ID
import asyncio
import xmlrpc.client
from threading import Thread, enumerate
from . import models


def _pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    dashboard = env["ir.module.module"].sudo().search([("name", "=", "board")])
    dashboard.button_install()
    inventory = env["ir.module.module"].sudo().search([("name", "=", "stock")])
    inventory.button_install()
    sales = env["ir.module.module"].sudo().search([("name", "=", "sale_management")])
    sales.button_install()
    purchase = env["ir.module.module"].sudo().search([("name", "=", "purchase")])
    purchase.button_install()


def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
