import pulsar
import asyncio
import requests

from odoo.tools.safe_eval import json
from odoo.exceptions import UserError
from odoo import api, fields, SUPERUSER_ID
from odoo import _

import logging

_logger = logging.getLogger(__name__)

TIMEOUT = 150

def account_and_part_decoder(buyer_id):
    account_info = None
    party_info = None
    account_api_end_point = f"https://api.addispay.et/Account/{buyer_id}"
    party_api_end_point = f"https://party.addispay.et/party/{buyer_id}"
    headers = {'User-Agent': 'party.addispay.et', 'X-Auth-Token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY0NzMyYzIzODNkZmQ5ZTQwOWRjMGZhNiIsImlhdCI6MTY4NTI2OTU3Nn0.tGNpNVOcUaf7mDvNF4jscOr0MnwVRrtIw9FVkaH4t08'}

    account_response = requests.post(account_api_end_point, timeout=50, headers=headers)

    if account_response.status_code == 200:
        account_info = account_response.json()
    elif account_response.status_code == 208:
        response_meaning = "Account already cleared"
        _logger.error("Addis Systems %s Account Information couldn't be Fetched:%s:%s", buyer_id, account_response.status_code, response_meaning)
    elif account_response.status_code == 400:
        response_meaning = "Account Record is not found"
        _logger.error("Addis Systems %s Account Information couldn't be Fetched:%s:%s", buyer_id, account_response.status_code, response_meaning)
    elif account_response.status_code == 502:
        response_meaning = "Bad Gateway"
        _logger.error("Addis Systems %s Account Information couldn't be Fetched:%s:%s", buyer_id, account_response.status_code, response_meaning)
    else:
        response_meaning = "API is not responding"
        _logger.error("Addis Systems %s Account Information couldn't be Fetched:%s:%s", buyer_id, account_response.status_code, response_meaning)

    party_response = requests.post(party_api_end_point, timeout=50, headers=headers)

    if party_response.status_code == 200:
        party_info = party_response.json()
    elif party_response.status_code == 208:
        response_meaning = "Party already cleared"
        _logger.error("Addis Systems %s Party Information couldn't be Fetched:%s:%s", buyer_id, party_response.status_code, response_meaning)
    elif party_response.status_code == 400:
        response_meaning = "Party Record is not found"
        _logger.error("Addis Systems %s Party Information couldn't be Fetched:%s:%s", buyer_id, party_response.status_code, response_meaning)
    elif party_response.status_code == 502:
        response_meaning = "Bad Gateway"
        _logger.error("Addis Systems %s Party Information couldn't be Fetched:%s:%s", buyer_id, party_response.status_code, response_meaning)
    else:
        response_meaning = "API is not responding"
        _logger.error("Addis Systems %s Party Information couldn't be Fetched:%s:%s", buyer_id, party_response.status_code, response_meaning)

    return [account_info, party_info]


def addis_systems_lead_pulsar_waiter(as_lead_env):
    lead_client = consumer = None
    try:
        lead_client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
    finally:
        if lead_client:
            topic_name = "persistent://addissystems/orders/order"
            consumer_configuration = {"subscription_name": 'addissystems'}
            try:
                consumer = lead_client.subscribe(topic_name, **consumer_configuration)
            except Exception as e:
                _logger.warning("Addis Systems topic subscription couldn't be achieved", e)
            finally:
                if consumer:
                    while True:
                        if msg := consumer.receive():
                            if isinstance(msg.data(), bytes):
                                data_str = msg.data().decode('utf-8')
                            else:
                                data_str = msg.data()

                            if lead_data_json := json.loads(data_str.replace("'", '"')):
                                if account_info := account_and_part_decoder(lead_data_json['buyer_ID']):
                                    if crm_lead_create(as_lead_env, lead_data_json, account_info):
                                        consumer.acknowledge(msg)



def crm_lead_create(as_lead_env, lead_data_json, account_info):
    account_detail = account_info[0][0]
    party_detail = account_info[1]

    crm_leads = None

    first_name = account_detail['Fname']
    last_name = account_detail['Lname']
    title = ''
    branch = party_detail['party'][0]['branch'][0]
    city = branch['address']['city']
    country = branch['address']['country']
    email = account_detail['email']
    phone = account_detail['phone']
    tin = party_detail['party'][0]['party']['tin_no']
    company_name = party_detail['party'][0]['party']['businessname']

    with as_lead_env.env.registry.cursor() as new_cr:
        env = api.Environment(new_cr, SUPERUSER_ID, {})

        partner_id = env['res.partner'].search(['|', ('name', '=', company_name), ('vat', '=', tin)], limit=1)

        if not partner_id:
            new_partner = env['res.partner'].create({
                'name': company_name,
                'company_type': 'company',
                'vat': str(tin),
                'phone': str(phone),
                'email': str(email)}
            )
            partner_id = new_partner

        addis_lead = {
            'name': str(f"Demo Request Lead from {company_name}"),
            'probability': 50.0,
            'partner_id': partner_id.id,
            'phone': phone or None,
            'mobile': phone or None,
            'campaign_id': env.ref('addis_systems_lead_digest.addis_systems_utm_campaign').id,
            'source_id': env.ref('addis_systems_lead_digest.addis_systems_utm_source').id,
        }

        crm_leads = env['crm.lead'].create(addis_lead)

        sales_all_document_users = env.ref('sales_team.group_sale_salesman_all_leads').users
        for user in sales_all_document_users:
            dead_line = fields.Date.today()
            activity_type = env.ref('mail.mail_activity_data_todo')
            if not env['mail.activity'].search([('summary', '=', _('New Demo Request from %s', crm_leads.partner_id.name)), ('res_id', '=', crm_leads.id)]):
                env['mail.activity'].create({
                    'display_name': 'Addis Systems New Leads',
                    'summary': _('New Demo Request from %s', crm_leads.partner_id.name),
                    'date_deadline': dead_line,
                    'user_id': user.id,
                    'res_id': crm_leads.id,
                    'res_model_id': env.ref('crm.model_crm_lead').id,
                    'activity_type_id': activity_type.id
                })

        return crm_leads

