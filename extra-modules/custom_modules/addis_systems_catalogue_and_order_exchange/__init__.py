from . import models, wizards
from odoo import api, SUPERUSER_ID


def _pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    purchase_requisition = env['ir.module.module'].sudo().search([('name', '=', 'purchase_requisition')])
    purchase_requisition.button_install()
