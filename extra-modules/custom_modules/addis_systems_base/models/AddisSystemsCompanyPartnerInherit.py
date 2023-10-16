from odoo import fields, models, api, _
from odoo.exceptions import UserError
import pulsar
import random

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

    def _init_odoobot(self):
        self.ensure_one()
        odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
        channel_info = self.env['mail.channel'].channel_get([odoobot_id, self.partner_id.id])
        channel = self.env['mail.channel'].browse(channel_info['id'])
        message = _("Hello,<br/>Addis System's chat helps employees collaborate efficiently. I'm here to help you discover its features.<br/><b>Try to send me an emoji</b> <span class=\"o_odoobot_command\">:)</span>")
        channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment", subtype_xmlid="mail.mt_comment")
        self.sudo().odoobot_state = 'onboarding_emoji'
        return channel


class AddisSystemsMailBot(models.AbstractModel):
    _inherit = "mail.bot"

    def _get_answer(self, record, body, values, command=False):
        # onboarding
        odoobot_state = self.env.user.odoobot_state
        if self._is_bot_in_private_channel(record):
            # main flow
            if odoobot_state == 'onboarding_emoji' and self._body_contains_emoji(body):
                self.env.user.odoobot_state = "onboarding_command"
                self.env.user.odoobot_failed = False
                return _("Great! 👍<br/>To access special commands, <b>start your sentence with</b> <span class=\"o_odoobot_command\">/</span>. Try getting help.")
            elif odoobot_state == 'onboarding_command' and command == 'help':
                self.env.user.odoobot_state = "onboarding_ping"
                self.env.user.odoobot_failed = False
                return _("Wow you are a natural!<br/>Ping someone with @username to grab their attention. <b>Try to ping me using</b> <span class=\"o_odoobot_command\">@AddisBot</span> in a sentence.")
            elif odoobot_state == 'onboarding_ping' and self._is_bot_pinged(values):
                self.env.user.odoobot_state = "onboarding_attachement"
                self.env.user.odoobot_failed = False
                return _("Yep, I am here! 🎉 <br/>Now, try <b>sending an attachment</b>, like a picture of your cute dog...")
            elif odoobot_state == 'onboarding_attachement' and values.get("attachment_ids"):
                self.env.user.odoobot_state = "idle"
                self.env.user.odoobot_failed = False
                return _("I am a simple bot, but if that's a dog, he is the cutest 😊 <br/>Congratulations, you finished this tour. You can now <b>close this chat window</b>. Enjoy discovering Addis Systems.")
            elif odoobot_state in (False, "idle", "not_initialized") and (_('start the tour') in body.lower()):
                self.env.user.odoobot_state = "onboarding_emoji"
                return _("To start, try to send me an emoji :)")
            # easter eggs
            elif odoobot_state == "idle" and body in ['❤️', _('i love you'), _('love')]:
                return _("Aaaaaw that's really cute but, you know, bots don't work that way. You're too human for me! Let's keep it professional ❤️")
            elif _('fuck') in body or "fuck" in body:
                return _("That's not nice! I'm a bot but I have feelings... 💔")
            # help message
            elif self._is_help_requested(body) or odoobot_state == 'idle':
                return _("Unfortunately, I'm just a bot 😞 I don't understand! If you need help discovering our product, please check "
                         "<a href=\"https://addissystems.et/documentation\" target=\"_blank\">our documentation</a> or "
                         "<a href=\"https://addissystems.et/slides\" target=\"_blank\">our videos</a>.")
            else:
                # repeat question
                if odoobot_state == 'onboarding_emoji':
                    self.env.user.odoobot_failed = True
                    return _("Not exactly. To continue the tour, send an emoji: <b>type</b> <span class=\"o_odoobot_command\">:)</span> and press enter.")
                elif odoobot_state == 'onboarding_attachement':
                    self.env.user.odoobot_failed = True
                    return _("To <b>send an attachment</b>, click on the <i class=\"fa fa-paperclip\" aria-hidden=\"true\"></i> icon and select a file.")
                elif odoobot_state == 'onboarding_command':
                    self.env.user.odoobot_failed = True
                    return _("Not sure what you are doing. Please, type <span class=\"o_odoobot_command\">/</span> and wait for the propositions. Select <span class=\"o_odoobot_command\">help</span> and press enter")
                elif odoobot_state == 'onboarding_ping':
                    self.env.user.odoobot_failed = True
                    return _("Sorry, I am not listening. To get someone's attention, <b>ping him</b>. Write <span class=\"o_odoobot_command\">@AddisBot</span> and select me.")
                return random.choice([
                    _("I'm not smart enough to answer your question.<br/>To follow my guide, ask: <span class=\"o_odoobot_command\">start the tour</span>."),
                    _("Hmmm..."),
                    _("I'm afraid I don't understand. Sorry!"),
                    _("Sorry I'm sleepy. Or not! Maybe I'm just trying to hide my unawareness of human language...<br/>I can show you features if you write: <span class=\"o_odoobot_command\">start the tour</span>.")
                ])
        return False


class AddisSystemsCompanyInherited(models.Model):
    _inherit = "res.company"

    vat = fields.Char(related="partner_id.vat", string="Tin Number", readonly=False, required=True)

    addis_system_id = fields.Char(string="Addis System ID", required=False, readonly=True)
    trade_name = fields.Char(string="Trade Name ", readonly=False, required=True, default=lambda self: self.env.company.name)

    def addis_system_connection_init(self):
        tenants_list_url = "http://192.168.100.209:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=100)
        if str(self.env.company.name).replace(" ", "").lower() in tenants_list.json():
            invoice_client = pulsar.Client("pulsar://192.168.100.209:6650")
            sales_client = pulsar.Client("pulsar://192.168.100.209:6650")
            client_dict = {"invoice_client": invoice_client, "sales_client": sales_client}
            print("------------------------------------------------------------------------------------------------------------------------------------------------")
            print("                                     Addis Systems Consumer Service has started for company", self.env.company.name, )
            print("------------------------------------------------------------------------------------------------------------------------------------------------")
            return client_dict
        else:
            _logger.warning('Company Information %s is the default value,Please configured your company information for exchange', self.env.company.name)

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
