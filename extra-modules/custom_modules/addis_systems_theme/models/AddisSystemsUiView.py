from odoo import fields, models, api, _
from odoo.exceptions import UserError
import pulsar

import logging
import requests

_logger = logging.getLogger(__name__)


class View(models.Model):
    _inherit = "ir.ui.view"

    @api.model
    def _render_template(self, template, values=None):
        if template in ["web.login", "web.webclient_bootstrap"]:
            if self.env.company.name:
                values["title"] = str(self.env.company.name)
            else:
                values["title"] = "Addis Systems"

            values["title"] = str(self.env.company.name)
        return super(View, self)._render_template(template, values)
