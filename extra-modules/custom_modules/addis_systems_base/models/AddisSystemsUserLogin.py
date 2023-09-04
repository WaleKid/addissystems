from odoo import fields, models, api
import asyncio
import requests

TIMEOUT = 150

class ResUsersLog(models.Model):
    _inherit = 'res.users.log'

    def _get_default_latitude_id(self):
        response = requests.get("http://ipinfo.io/json", timeout=TIMEOUT).json()
        latitude, longitude = response["loc"].split(',')
        return latitude
    def _get_default_longitude_id(self):
        response = requests.get("http://ipinfo.io/json", timeout=TIMEOUT).json()
        latitude, longitude = response["loc"].split(',')
        return longitude

    latitude = fields.Char(string="Latitude", required=True, default=_get_default_latitude_id)
    longitude = fields.Char(string="Longitude",  required=True, default=_get_default_longitude_id)
