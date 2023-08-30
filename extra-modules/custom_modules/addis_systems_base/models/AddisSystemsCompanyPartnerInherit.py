from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class View(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def _render_template(self, template, values=None):
        if template in ['web.login', 'web.webclient_bootstrap']:
            if self.env.company.name:
                values["title"] = str(self.env.company.name)
            else:
                values["title"] = "Addis Systems"

            values["title"] = str(self.env.company.name)
        return super(View, self)._render_template(template, values)


class AddisSystemsCompanyInherited(models.Model):
    _inherit = 'res.company'

    vat = fields.Char(related='partner_id.vat', string="Tin Number", readonly=False, required=True)

    addis_system_id = fields.Char(string="Addis System ID", required=False, readonly=True)
    trade_name = fields.Char(string="Trade Name ", readonly=False, required=True, default=lambda self: self.env.company.name)

    def addis_system_connection_init(self):
        print("------------------------------------------------------------------------------------------------------------------------------------------------")
        print("Addis Systems Service Listener has started for company", self.env.company.name)
        print("------------------------------------------------------------------------------------------------------------------------------------------------")

    @api.model_create_multi
    def create(self, vals_list):
        global action_create
        for vals in vals_list:
            action_create = super(AddisSystemsCompanyInherited, self).create(vals)
            if action_create.vat and action_create.company_type == 'company':
                if not action_create.vat.isdigit():
                    raise UserError(_("Standard Ethiopian Tin Number can only contain Numerical values"))
                elif len(action_create.vat) != 13 or len(action_create.vat) != 10:
                    raise UserError(_(str("Standard Ethiopian Tin Number should be 10 or 13 digits in length")))
                else:
                    return action_create
            else:
                return action_create

    def write(self, values):
        action_write = super(AddisSystemsCompanyInherited, self).write(values)
        if values.get('vat') and values.get('company_type') == 'company':
            if not values.get('vat').isdigit():
                raise UserError(_("Standard Ethiopian Tin Number can only contain Numerical values"))
            elif len(values.get('vat')) != 13 and len(values.get('vat')) != 10:
                raise UserError(_("Standard Ethiopian Tin Number should be 10 or 13 digits in length"))
            else:
                return action_write
        else:
            return action_write


class AddisSystemsPartnerInherited(models.Model):
    _inherit = 'res.partner'

    vat = fields.Char(string="Tin Number", readonly=False, required=False)

    @api.model_create_multi
    def create(self, vals_list):
        global action_create
        for vals in vals_list:
            action_create = super(AddisSystemsPartnerInherited, self).create(vals)
            if action_create.vat and action_create.company_type == 'company':
                if not action_create.vat.isdigit():
                    raise UserError(_("Standard Ethiopian Tin Number can only contain Numerical values"))
                elif len(action_create.vat) != 13 and len(action_create.vat) != 10:
                    raise UserError(_(str("Standard Ethiopian Tin Number should be 10 or 13 digits in length")))
                else:
                    return action_create
            else:
                return action_create

    def write(self, values):
        action_write = super(AddisSystemsPartnerInherited, self).write(values)
        if values.get('vat') and values.get('company_type') == 'company':
            if not values.get('vat').isdigit():
                raise UserError(_("Standard Ethiopian Tin Number can only contain Numerical values"))
            elif len(values.get('vat')) != 13 and len(values.get('vat')) != 10:
                raise UserError(_(str("Standard Ethiopian Tin Number should be 10 or 13 digits in length")))
            else:
                return action_write
        else:
            return action_write
