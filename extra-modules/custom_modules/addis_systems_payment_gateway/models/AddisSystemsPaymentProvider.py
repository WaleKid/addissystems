import logging
import re

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment_adyen.const import API_ENDPOINT_VERSIONS

_logger = logging.getLogger(__name__)

class AddisSystemsPaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('addispay', "Addis Pay")], ondelete={'addispay': 'set default'})
    addispay_merchant_account = fields.Char(
        string="Addis Pay Merchant Account",
        help="The code of the merchant account to use with this provider",
        required_if_provider='addispay', groups='base.group_system')
    addispay_api_key = fields.Char(
        string="Addis Pay API Key", help="The API key of the webservice user", required_if_provider='addispay',
        groups='base.group_system')
    addispay_client_key = fields.Char(
        string="Addis Pay Client Key", help="The client key of the webservice user",
        required_if_provider='addispay')
    addispay_hmac_key = fields.Char(
        string="Addis Pay HMAC Key", help="The HMAC key of the webhook", required_if_provider='addispay',
        groups='base.group_system')
    addispay_checkout_api_url = fields.Char(
        string="Addis Pay Checkout API URL", help="The base URL for the Checkout API endpoints",
        required_if_provider='addispay')
    addispay_recurring_api_url = fields.Char(
        string="Addis Pay Recurring API URL", help="The base URL for the Recurring API endpoints",
        required_if_provider='addispay')