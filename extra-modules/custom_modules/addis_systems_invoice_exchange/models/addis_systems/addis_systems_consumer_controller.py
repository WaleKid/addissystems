import pulsar
import io
import avro.schema

from odoo.tools.safe_eval import json
from odoo.exceptions import UserError
from odoo import api, SUPERUSER_ID, _

import logging
import asyncio
import requests

from ..avro_schema import InvoiceAcknowledgement

_logger = logging.getLogger(__name__)
TIMEOUT = 150

def vendor_bill_consumer_asynch(vb_env):
    async def invoice_decoder(acknowledgement_number):
        decoded_invoice = None
        base_endpoint_url = "https://invoice-reg.api.qa.addispay.et/getInvoice/"
        api_end_point = base_endpoint_url + acknowledgement_number
        response = requests.get(api_end_point, timeout=TIMEOUT)
        if response.status_code == 200:
            decoded_invoice = response.json()
        elif response.status_code == 208:
            response_meaning = "Invoice already cleared"
            _logger.error("Addis Systems %s Invoice couldn't be decoded:%s:%s", acknowledgement_number, response.status_code, response_meaning)
        elif response.status_code == 400:
            response_meaning = "Record is not found"
            _logger.error("Addis Systems %s Invoice couldn't be decoded:%s:%s", acknowledgement_number, response.status_code, response_meaning)
        elif response.status_code == 502:
            response_meaning = "Bad Gateway"
            _logger.error("Addis Systems %s Invoice couldn't be decoded:%s:%s", acknowledgement_number, response.status_code, response_meaning)
        else:
            response_meaning = "API End Point is not responding"
            _logger.error("Addis Systems %s Invoice couldn't be decoded:%s:%s", acknowledgement_number, response.status_code, response_meaning)

        return decoded_invoice

    def vendor_bill_pulsar_waiter(vendor_bill_env):
        vb_client = consumer = None
        invoice_ack__avro = InvoiceAcknowledgement.invoice_acknowledgement_schema
        schema = avro.schema.parse(json.dumps(invoice_ack__avro))
        company_name = str(vendor_bill_env.env.company.name.replace(' ', '').lower())

        try:
            vb_client = pulsar.Client("pulsar://196.189.124.178:6650")
        except Exception as e:
            raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
        finally:
            if vb_client:
                topic_name = "persistent://addisadmin/invoice/exchange"
                consumer_configuration = {"subscription_name": company_name}
                try:
                    consumer = vb_client.subscribe(topic_name, **consumer_configuration)
                except Exception as e:
                    _logger.warning("Addis Systems topic subscription couldn't be achieved", e)
                finally:
                    if consumer:
                        while True:
                            if msg := consumer.receive():
                                key = msg.properties()['key']
                                if company_name == key:
                                    bytes_writer = io.BytesIO(msg.data())
                                    decoder = avro.io.BinaryDecoder(bytes_writer)
                                    datum_reader = avro.io.DatumReader(schema)
                                    datajson = datum_reader.read(decoder)

                                    if datajson and datajson['Signed_invoice']:
                                        if decoder := asyncio.run(invoice_decoder(datajson['AckNo'])):
                                            if vendor_bill_create(vendor_bill_env, datajson, decoder):
                                                consumer.acknowledge(msg)
                                else:
                                    consumer.negative_acknowledge(msg)

    def vendor_bill_create(vendor_bill_env, vb_mor_data, vb_decoded_data):
        invoice_reference = vb_decoded_data['Invoice_Reference']
        invoice_description = vb_decoded_data['Invoice_Desc']
        invoice_source_process = vb_decoded_data['Invoice_source_process']
        seller_info = vb_decoded_data["Seller"]
        buyer_info = vb_decoded_data['Buyer']
        payee_info = vb_decoded_data['Payee']
        delivery_info = vb_decoded_data['Delivery_info']
        payment_info = vb_decoded_data['Payment_info']
        vat_description = vb_decoded_data['Vat_breakdown']

        with vendor_bill_env.env.registry.cursor() as new_cr:
            env = api.Environment(new_cr, SUPERUSER_ID, {})
            if not env['account.move'].search([('acknowledgement_number', '=', vb_mor_data['AckNo'])]):
                partner_id = env['res.partner'].search(['|', ('name', '=', seller_info['company_name']), ('vat', '=', seller_info['tin_no'])], limit=1)
                if not partner_id:
                    new_partner = env['res.partner'].create({
                        'name': seller_info['company_name'],
                        'company_type': 'company',
                        'vat': str(seller_info['tin_no']),
                        'phone': str(seller_info['tin_no']),
                        'email': str(seller_info['tin_no'])}
                    )
                    partner_id = new_partner

                vendor_bill_vals = {
                    'partner_id': partner_id.id,
                    'invoice_date': invoice_description['Inv_Dt'],
                    'invoice_date_due': invoice_description['payment_due_Dt'],
                    'payment_reference': '',
                    'IRN': vb_mor_data['IRN'],
                    'acknowledgement_number': vb_mor_data['AckNo'],
                    'acknowledgement_date': vb_mor_data['AckDt'],
                    'signed_invoice': vb_mor_data['Signed_invoice'],
                    'signed_qr_code': vb_mor_data['Signed_QRCode'],
                    'created_date': vb_mor_data['Created_Date'],
                    'created_by': vb_mor_data['Created_by'],
                    'invoice_status': vb_mor_data['Inv_Status'],
                    'move_type': 'in_invoice',
                    'ref': invoice_description['Invoice_ref'],
                    'to_check': True,
                    'amount_tax': vat_description['Vat_breakdown_amount'],
                    'state': 'draft',
                    'company_id': vendor_bill_env.env.company.id,
                }

                account_move = env['account.move'].create(vendor_bill_vals)

                product_lines = []

                for products in vb_decoded_data['Invoice_line']:
                    product = env['product.template'].search([('name', '=', products["hsncode"])], limit=1) or env['product.template'].create({
                        'name': products["product_name"],
                        'sale_ok': False,
                        'purchase_ok': True,
                        'invoice_policy': products["invoicing_policy"],
                        'description_purchase': products["Product_desc"],
                        'detailed_type': products["product_type"],
                        'list_price': products['unit_price'],
                        'standard_price': products['unit_price']
                    })

                    tax_id = env['account.tax'].search([('amount_type', '=', products['amount_type']), ('type_tax_use', '!=', products['tax_type']), ('amount', '=', products['tax_amount'])], limit=1)
                    prod_line = {
                        'product_id': env['product.product'].search([('product_tmpl_id', '=', product.id)], limit=1).id,
                        'quantity': products["qty"],
                        'price_unit': products["unit_price"],
                        'tax_ids': tax_id or None,
                        'move_id': account_move.id,
                    }

                    product_lines.append(prod_line)

                env['account.move.line'].create(product_lines)

                accountant_manager_group_users = env.ref('account.group_account_manager').users
                for user in accountant_manager_group_users:
                    dead_line = account_move.invoice_date_due or account_move.date
                    activity_type = env.ref('mail.mail_activity_data_todo')
                    for activity in activity_type:
                        env['mail.activity'].create({
                            'display_name': 'Addis Systems Vendor Bill',
                            'summary': _('New Vendor Bill to Confirm from %s', account_move.partner_id.name),
                            'date_deadline': dead_line,
                            'user_id': user.id,
                            'res_id': account_move.id,
                            'res_model_id': env.ref('account.model_account_move').id,
                            'activity_type_id': activity.id
                        })

                return account_move

    vendor_bill_pulsar_waiter(vb_env,)


def credit_note_consumer_asynch(cb_env):
    async def credit_note_decoder(acknowledgement_number):
        decoded_invoice = None
        base_endpoint_url = "https://invoice-reg.api.qa.addispay.et/getRefund/"
        api_end_point = base_endpoint_url + acknowledgement_number

        response = requests.get(api_end_point, timeout=TIMEOUT)

        if response.status_code == 200:
            decoded_invoice = response.json()
        elif response.status_code == 400:
            if response.json() == "Invoice already cleared":
                response_meaning = "Record is not found"
                _logger.error("Addis Systems %s Invoice couldn't be decoded:%s:%s", acknowledgement_number, response.status_code, response_meaning)
            else:
                response_meaning = "Record is not found"
                _logger.error("Addis Systems %s Refund couldn't be decoded:%s:%s", acknowledgement_number, response.status_code, response_meaning)
        elif response.status_code == 502:
            response_meaning = "Bad Gateway"
            _logger.error("Addis Systems %s Refund couldn't be decoded:%s:%s", acknowledgement_number, response.status_code, response_meaning)
        else:
            response_meaning = "API End Point is not responding"
            _logger.error("Addis Systems %s Refund couldn't be decoded:%s:%s", acknowledgement_number, response.status_code, response_meaning)

        return decoded_invoice

    def credit_note_pulsar_waiter(credit_bill_env):
        vb_client = consumer = None
        invoice_ack_schema = InvoiceAcknowledgement.invoice_acknowledgement_schema
        schema = avro.schema.parse(json.dumps(invoice_ack_schema))
        company_name = str(credit_bill_env.env.company.name.replace(' ', '').lower())

        try:
            vb_client = pulsar.Client("pulsar://196.189.124.178:6650")
        except Exception as e:
            raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
        finally:
            if vb_client:
                topic_name = "persistent://addisadmin/refund/exchange"
                consumer_configuration = {"subscription_name": company_name}
                try:
                    consumer = vb_client.subscribe(topic_name, **consumer_configuration)
                except Exception as e:
                    _logger.warning("Addis Systems topic subscription couldn't be achieved", e)
                finally:
                    if consumer:
                        while True:
                            if msg := consumer.receive():
                                key = msg.properties()['key']
                                if company_name == key:
                                    bytes_writer = io.BytesIO(msg.data())
                                    decoder = avro.io.BinaryDecoder(bytes_writer)
                                    datum_reader = avro.io.DatumReader(schema)
                                    datajson = datum_reader.read(decoder)

                                    if datajson and datajson['Signed_invoice']:
                                        decoder = asyncio.run(credit_note_decoder(datajson['AckNo']))
                                        if decoder and credit_note_create(credit_bill_env, datajson, decoder):
                                            consumer.acknowledge(msg)
                                else:
                                    consumer.negative_acknowledge(msg)

    def credit_note_create(credit_bill_env, vb_mor_data, vb_decoded_data):
        refund_reference = vb_decoded_data['Invoice_Reference']
        refund_description = vb_decoded_data['Invoice_Desc']
        refund_source_process = vb_decoded_data['Invoice_source_process']
        seller_info = vb_decoded_data["Seller"]
        buyer_info = vb_decoded_data['Buyer']
        vat_description = vb_decoded_data['Vat_breakdown']


        with credit_bill_env.env.registry.cursor() as new_cr:
            env = api.Environment(new_cr, SUPERUSER_ID, {})
            invoice_record = env['account.move'].search([('name', '=', refund_reference['Seller_ref_no'])])
            if not env['account.move'].search([('acknowledgement_number', '=', vb_mor_data['AckNo'])]) and invoice_record:
                credit_bill_vals = {
                    'partner_id': invoice_record.partner_id.id,
                    'invoice_date': refund_description['Inv_Dt'],
                    'invoice_date_due': refund_description['payment_due_Dt'],
                    'payment_reference': '',
                    'reversed_entry_id': invoice_record.id,
                    'IRN': vb_mor_data['IRN'],
                    'acknowledgement_number': vb_mor_data['AckNo'],
                    'acknowledgement_date': vb_mor_data['AckDt'],
                    'signed_invoice': vb_mor_data['Signed_invoice'],
                    'signed_qr_code': vb_mor_data['Signed_QRCode'],
                    'created_date': vb_mor_data['Created_Date'],
                    'created_by': vb_mor_data['Created_by'],
                    'invoice_status': vb_mor_data['Inv_Status'],
                    'move_type': 'out_refund',
                    'ref': refund_reference['Buy_ref_no'],
                    'to_check': True,
                    'amount_tax': vat_description['Vat_breakdown_amount'],
                    'state': 'draft',
                    'company_id': cb_env.env.company.id,
                }

                credit_note = env['account.move'].create(credit_bill_vals)

                product_lines = []

                for products in vb_decoded_data['Invoice_line']:
                    product = env['product.template'].search([('name', '=', products["product_name"])], limit=1) or env['product.template'].create({
                        'name': products["product_name"],
                        'sale_ok': False,
                        'purchase_ok': True,
                        'invoice_policy': products["invoicing_policy"],
                        'description_purchase': products["Product_desc"],
                        'detailed_type': products["product_type"],
                        'list_price': products['unit_price'],
                        'standard_price': products['unit_price']
                    })

                    tax_id = env['account.tax'].search([('amount_type', '=', products['amount_type']), ('type_tax_use', '!=', products['tax_type']), ('amount', '=', products['tax_amount'])], limit=1)
                    product_line = {
                        'product_id': env['product.product'].search([('product_tmpl_id', '=', product.id)], limit=1).id,
                        'quantity': products["qty"],
                        'price_unit': products["unit_price"],
                        'tax_ids': tax_id or None,
                        'move_id': credit_note.id
                    }
                    product_lines.append(product_line)

                env['account.move.line'].create(product_lines)

                accountant_manager_group_users = env.ref('account.group_account_manager').users
                for user in accountant_manager_group_users:
                    dead_line = credit_note.invoice_date_due or credit_note.date
                    activity_type = env.ref('mail.mail_activity_data_todo')
                    for activity in activity_type:
                        env['mail.activity'].create({
                            'display_name': 'Addis Systems Vendor Bill',
                            'summary': _('New Refund Bill to Confirm from %s', credit_note.partner_id.name),
                            'date_deadline': dead_line,
                            'user_id': user.id,
                            'res_id': credit_note.id,
                            'res_model_id': env.ref('account.model_account_move').id,
                            'activity_type_id': activity.id
                        })

                return credit_note

    credit_note_pulsar_waiter(cb_env,)


