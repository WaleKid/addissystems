from odoo import api, SUPERUSER_ID
from . import models


def _pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})

    env.company.external_report_layout_id = env.ref('addis_systems_theme.addis_systems_report').id


def _post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
