from odoo import fields, models, api
import asyncio
import requests

TIMEOUT = 150


class ResUsersLog(models.Model):
    _inherit = 'res.users.log'

    @staticmethod
    def _get_default_latitude_id():
        response = requests.get("http://ipinfo.io/json", timeout=TIMEOUT).json()
        latitude, longitude = response["loc"].split(',')
        return latitude or '0.0000'

    @staticmethod
    def _get_default_longitude_id():
        response = requests.get("http://ipinfo.io/json", timeout=TIMEOUT).json()
        latitude, longitude = response["loc"].split(',')
        return longitude or '00.0000'

    latitude = fields.Char(string="Latitude", required=True, default=_get_default_latitude_id)
    longitude = fields.Char(string="Longitude", required=True, default=_get_default_longitude_id)
