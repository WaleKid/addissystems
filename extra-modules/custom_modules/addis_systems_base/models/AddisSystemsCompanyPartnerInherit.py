from odoo import fields, models, api, _
from odoo.exceptions import UserError
import pulsar

import logging
import requests

_logger = logging.getLogger(__name__)

TIMEOUT = 150


class ResUsersLog(models.Model):
    _inherit = "res.users.log"

    @staticmethod
    def _get_default_latitude_id():
        response = requests.get("http://ipinfo.io/json", timeout=TIMEOUT).json()
        latitude, longitude = response["loc"].split(",")
        return latitude or "0.0000"

    @staticmethod
    def _get_default_longitude_id():
        response = requests.get("http://ipinfo.io/json", timeout=TIMEOUT).json()
        latitude, longitude = response["loc"].split(",")
        return longitude or "00.0000"

    latitude = fields.Char(string="Latitude", required=True, default=_get_default_latitude_id)
    longitude = fields.Char(string="Longitude", required=True, default=_get_default_longitude_id)


class ResUsers(models.Model):
    _inherit = "res.users"

    latitude = fields.Char(related="log_ids.latitude", string="Latitude", readonly=True)
    longitude = fields.Char(related="log_ids.longitude", string="Longitude", readonly=True)


class AddisSystemsCompanyInherited(models.Model):
    _inherit = "res.company"

    vat = fields.Char(related="partner_id.vat", string="Tin Number", readonly=False, required=True)

    addis_system_id = fields.Char(string="Addis System ID", required=False, readonly=True)
    trade_name = fields.Char(string="Trade Name ", readonly=False, required=True, default=lambda self: self.env.company.name)

    def addis_system_connection_init(self):
        tenants_list_url = "http://192.168.100.208:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=100)
        if str(self.env.company.name).replace(" ", "").lower() in tenants_list.json():
            invoice_client = pulsar.Client("pulsar://192.168.100.208:6650")
            sales_client = pulsar.Client("pulsar://192.168.100.208:6650")
            client_dict = {"invoice_client": invoice_client, "sales_client": sales_client}
            print("------------------------------------------------------------------------------------------------------------------------------------------------")
            print("                                     Addis Systems Consumer Service has started for company", self.env.company.name, )
            print("------------------------------------------------------------------------------------------------------------------------------------------------")
            return client_dict

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            action_create = super(AddisSystemsCompanyInherited, self).create(vals)
            if not action_create.vat or action_create.company_type != "company":
                return action_create
            if not action_create.vat.isdigit():
                raise UserError(_("Standard Ethiopian Tin Number can only contain Numerical values"))
            else:
                raise UserError(_("Standard Ethiopian Tin Number should be 10 or 13 digits in length"))

    def write(self, values):
        action_write = super(AddisSystemsCompanyInherited, self).write(values)
        if not values.get("vat") or values.get("company_type") != "company":
            return action_write
        if not values.get("vat").isdigit():
            raise UserError(_("Standard Ethiopian Tin Number can only contain Numerical values"))
        elif len(values.get("vat")) not in [13, 10]:
            raise UserError(_("Standard Ethiopian Tin Number should be 10 or 13 digits in length"))
        else:
            return action_write


class AddisSystemsPartnerInherited(models.Model):
    _inherit = "res.partner"

    vat = fields.Char(string="Tin Number", readonly=False, required=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            action_create = super(AddisSystemsPartnerInherited, self).create(vals)
            if not action_create.vat or action_create.company_type != "company":
                return action_create
            if not action_create.vat.isdigit():
                raise UserError(_("Standard Ethiopian Tin Number can only contain Numerical values"))
            elif len(action_create.vat) not in [13, 10]:
                raise UserError(_("Standard Ethiopian Tin Number should be 10 or 13 digits in length"))
            else:
                return action_create

    def write(self, values):
        action_write = super(AddisSystemsPartnerInherited, self).write(values)
        if not values.get("vat") or values.get("company_type") != "company":
            return action_write
        if not values.get("vat").isdigit():
            raise UserError(_("Standard Ethiopian Tin Number can only contain Numerical values"))
        elif len(values.get("vat")) not in [13, 10]:
            raise UserError(_("Standard Ethiopian Tin Number should be 10 or 13 digits in length"))
        else:
            return action_write
