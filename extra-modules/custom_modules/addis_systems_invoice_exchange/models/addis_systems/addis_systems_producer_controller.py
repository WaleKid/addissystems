from odoo.tools.safe_eval import json
from datetime import datetime
from odoo.exceptions import UserError
from odoo import fields

import avro.schema
from avro.io import DatumWriter
import io
import requests

import pulsar

import logging

from ..avro_schema import InvoiceSchema
from ..avro_schema import RefundSchema
from ..avro_schema import logSchema

_logger = logging.getLogger(__name__)


async def check_partner_electronic_invoice_user(partner):
    tenants_list_url = "http://196.189.124.178:8080/admin/v2/tenants"
    tenants_list = requests.get(tenants_list_url, timeout=150)
    return str(partner.name).replace(' ', '').lower() in tenants_list.json()


#   ----------------------------------------    Invoice Handler    ----------------------------------------

async def invoice_producer(invoice_id):
    successful_invoice = False
    invoice_line = []
    client = None

    line_sequence_number = 0
    for line in invoice_id.invoice_line_ids:
        line_sequence_number = line_sequence_number + 1
        invoice_line.append({
            "sno": str(line_sequence_number),
            "hsncode": '',
            "barcode": str(line.product_id.barcode),
            "invoicing_policy": str(line.product_id.product_tmpl_id.invoice_policy),
            "Product_desc": str(line.product_id.product_tmpl_id.description_sale or ''),
            "product_name": str(line.product_id.product_tmpl_id.name),
            "product_type": str(line.product_id.product_tmpl_id.detailed_type),
            "product_category": str(line.product_id.product_tmpl_id.categ_id.name),
            "qty": str(line.quantity),
            "unit": str(line.product_uom_id.name),
            "unit_price": str(line.price_unit),
            "amount_type": str(line.tax_ids.amount_type if line.tax_ids else ""),
            "tax_type": str(line.tax_ids.type_tax_use if line.tax_ids else ""),
            "tax_scope": str(line.tax_ids.tax_scope if line.tax_ids else ""),
            "tax_amount": str(line.tax_ids.amount if line.tax_ids else ""),
            "Line_allowance_code": "",
            "Line_allowance_reason": "",
            "Line_allowance_amount": '',
            "Line_charge_code": '',
            "Line_charge_reason": '',
            "Line_charge_amount": '',
            "total_price": str(line.price_subtotal or ""),
        })

    invoice_data = {
        "Invoice_Reference": {
            "Buy_ref_no": "",
            "Project_ref_no": "",
            "cont_ref_no": "",
            "PO_ref_no": "",
            "Sellers_order_ref_no": str(invoice_id.name or ""),
            "Rec_advice_ref_no": "",
            "Disp_advice_ref_no": "",
            "Tender_ref_no": "",
            "Invo_obj_ref_no": str(invoice_id.name or ""),
            "invoice_declaration": "",
        },
        "Invoice_Desc": {
            "taxschema": str(datetime.now()),
            "InvType": str(invoice_id.move_type),
            "Invoice_no": str(invoice_id.id),
            "Invoice_ref": str(invoice_id.name),
            "Inv_Dt": str(invoice_id.invoice_date or ""),
            "payment_due_Dt": str(invoice_id.invoice_date_due or ""),
        },
        "Invoice_source_process": {
            "process": "AR",
            "SupType": "B2B",
            "proccess_reference_no": "",
        },
        "Seller": {
            "tin_no": str(invoice_id.company_id.vat or ""),
            "license_number": str(invoice_id.company_id.company_registry or ""),
            "vat_reg_no": str(invoice_id.company_id.company_registry or ""),
            "vat_reg_Dt": "WHOLESALE",
            "address": str(invoice_id.company_id.city or ""),
            "location": str(invoice_id.company_id.street2 or ""),
            "email": str(invoice_id.company_id.email or ""),
            "company_name": str(invoice_id.env.company.name).replace(' ', '').lower(),
            "user_name": str(invoice_id.env.user.name),
        },
        "Buyer": {
            "tin_no": str(invoice_id.partner_id.vat or ""),
            "vat_reg_no": str(invoice_id.partner_id.vat or ""),
            "address": str(invoice_id.partner_id.country_id.name or ""),
            "location": str(invoice_id.partner_id.state_id.name or ""),
            "phone_no": str(invoice_id.partner_id.phone or None),
            "email": str(invoice_id.partner_id.email or None),
            "company_name": str(invoice_id.partner_id.name).replace(' ', '').lower(),
        },
        "Payee": {
            "id": "",
            "name": str(invoice_id.payment_reference or ""),
            "registration_number": "",
            "bank": "",
            "bank_account": "",
            "legal_registration": "",
        },
        "Delivery_info": {
            "Delivery_note_number": "",
            "delivery_date": "",
            "delivery_location": "",
            "delivery_address": "",
        },
        "Payment_info": {
            "payment_means": "",
            "payer_account": "",
            "payment_term": "",
        },
        "Invoice_total": str(invoice_id.amount_total or ""),
        "Vat_breakdown": {
            "Vat_category_code": "",
            "Vat_reason_code": "",
            "Vat_reason_text": "",
            "Vat_breakdown_amount": str(invoice_id.amount_tax or ""),
        },
        "Invoice_allowance": "",
        "Invoice_charge": "",
        "Invoice_line": invoice_line,
    }

    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
    finally:
        if client:
            invoice_produced = await _invoice_mor_producer(invoice_id, client, invoice_data)
            if invoice_produced:
                invoice_acknowledged_consumed = await _invoice_mor_consumer(invoice_id, client)
                successful_invoice = bool(invoice_acknowledged_consumed)
            client.close()
    return successful_invoice

async def _invoice_mor_producer(invoice_id, client, invoice_data):
    invoice_avro = InvoiceSchema.invoice_schema
    inv_schema = avro.schema.parse(json.dumps(invoice_avro))
    own_producer = None
    mor_producer = None
    log_producer = None
    invoice_produced = False

    try:
        own_producer = client.create_producer(
            "persistent://" + str(invoice_id.env.company.name).replace(' ', '').lower() + "/invoice/sales")
        mor_producer = client.create_producer("persistent://mor/invoice/invoice")
    except Exception as e:
        _logger.warning("%s:Addis Systems couldn't create producers!", e)
    finally:
        if own_producer and mor_producer:
            writer = DatumWriter(inv_schema)
            bytes_writer = io.BytesIO()
            encoder = avro.io.BinaryEncoder(bytes_writer)
            writer.write(invoice_data, encoder)
            own_producer.send(bytes_writer.getvalue())
            mor_producer.send(bytes_writer.getvalue(), properties={"key": "invoice_key"})

            invoice_produced = True

            # Log Tracking Producer

            # log_avro_schema = logSchema.log_tracking_schema
            # log_schema = avro.schema.parse(json.dumps(log_avro_schema))
            #
            # try:
            #     log_producer = client.create_producer("persistent://pulsar/default/LogTracking")
            # except Exception as e:
            #     _logger.warning("%s:Addis Systems couldn't create producers!", e)
            # finally:
            #     if log_producer:
            #         log_data = {
            #             "InvoiceCreatedDate": str(fields.Datetime.now()),
            #             "InvoiceID": str(invoice_id.name or None),
            #             "CompanyName": str(invoice_id.env.company.name).replace(' ', '').lower(),
            #             "ErrorResponse": "",
            #             "ErrorStatus": {
            #                 "sentStatus": {
            #                     "Sent_INV": "True",
            #                     "Sent_INV_AT": str(fields.Datetime.now())
            #                 },
            #                 "received_Status": {
            #                     "Received_INV": "",
            #                     "Received_INV_AT": ""
            #                 },
            #                 "Ack_gen_Status": {
            #                     "Ack_Gen_INV": "",
            #                     "Ack_Gen_INV_AT": ""
            #                 },
            #                 "Ack_save_Status": {
            #                     "Ack_Save_INV": "",
            #                     "Ack_Save_INV_AT": ""
            #                 },
            #                 "Ack_Sent_Status": {
            #                     "Ack_Sent_INV": "",
            #                     "Ack_Sent_INV_AT": ""
            #                 },
            #                 "Ack_Consume_Status": {
            #                     "Ack_Consume_INV": "",
            #                     "Ack_Consume_INV_AT": ""
            #                 },
            #                 "Ack_Exchange": {
            #                     "Ack_Exchange_INV": "",
            #                     "Ack_Exchange_INV_AT": ""
            #                 },
            #                 "Ack_Exchange_Cons": {
            #                     "Ack_Exchange_Cons_INV": "",
            #                     "Ack_Exchange_Cons_INV_AT": ""
            #                 },
            #                 "Ack_Send_To_Vendor": {
            #                     "Ack_Send_To_Vendor_INV": "",
            #                     "Ack_Send_To_Vendor_INV_AT": ""
            #                 },
            #                 "Ack_Verify_Status": {
            #                     "Ack_Verify_INV": "",
            #                     "Ack_Verify_INV_AT": ""
            #                 },
            #                 "Ack_StatusUpdate_Status": {
            #                     "Ack_StatusUpdate_INV": "",
            #                     "Ack_StatusUpdate_INV_AT": ""
            #                 },
            #             },
            #         }
            #         writer = DatumWriter(log_schema)
            #         bytes_writer = io.BytesIO()
            #         encoder = avro.io.BinaryEncoder(bytes_writer)
            #         writer.write(log_data, encoder)
            #         log_producer.send(bytes_writer.getvalue())

            own_producer.close()
            mor_producer.close()
            # log_producer.close()
    return invoice_produced

async def _invoice_mor_consumer(invoice_id, client):
    consumer = None
    topic_name = "persistent://" + str(invoice_id.env.company.name).replace(' ', '').lower() + "/invoice/invoiceack"
    consumer_conf = {"subscription_name": str(invoice_id.env.company.name).replace(' ', '').lower()}

    try:
        consumer = client.subscribe(topic_name, **consumer_conf)
    except Exception:
        _logger.warning("Addis Systems topic subscription couldn't be achieved %s, %s", topic_name, consumer_conf)
    finally:
        if consumer:
            msg = consumer.receive()

            if isinstance(msg.data(), bytes):
                data_string = msg.data().decode('utf-8')
            else:
                data_string = msg.data()

            datajson = json.loads(data_string)
            is_e_invoice = await check_partner_electronic_invoice_user(invoice_id.partner_id)

            invoice_id.IRN = datajson['IRN']
            invoice_id.acknowledgement_number = datajson['AckNo']
            invoice_id.acknowledgement_date = datajson['AckDt']
            invoice_id.signed_invoice = datajson['Signed_invoice']
            invoice_id.signed_qr_code = datajson['Signed_QRCode']
            invoice_id.created_date = datajson['Created_Date']
            invoice_id.created_by = datajson['Created_by']
            invoice_id.invoice_status = 'registered' if datajson['Inv_Status'] == 'Registered' else 'failed'
            invoice_id.partner_e_invoicing = is_e_invoice
            consumer.acknowledge(msg)
            return True

async def invoice_log_tracking_producer_consume(invoice_id):
    log_avro_schema = logSchema.log_tracking_schema
    schema = avro.schema.parse(json.dumps(log_avro_schema))
    log_producer = None
    client = None
    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
    finally:
        if client:
            try:
                log_producer = client.create_producer("persistent://pulsar/default/LogTracking")
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if log_producer:
                    log_data = {
                        "InvoiceCreatedDate": str(fields.Datetime.now()),
                        "InvoiceID": str(invoice_id.name or None),
                        "CompanyName": str(invoice_id.env.company.name).replace(' ', '').lower(),
                        "ErrorResponse": "",
                        "ErrorStatus": {
                            "sentStatus": {
                                "Sent_INV": "",
                                "Sent_INV_AT": ""
                            },
                            "received_Status": {
                                "Received_INV": "",
                                "Received_INV_AT": ""
                            },
                            "Ack_gen_Status": {
                                "Ack_Gen_INV": "",
                                "Ack_Gen_INV_AT": ""
                            },
                            "Ack_save_Status": {
                                "Ack_Save_INV": "",
                                "Ack_Save_INV_AT": ""
                            },
                            "Ack_Sent_Status": {
                                "Ack_Sent_INV": "",
                                "Ack_Sent_INV_AT": ""
                            },
                            "Ack_Consume_Status": {
                                "Ack_Consume_INV": "True",
                                "Ack_Consume_INV_AT": str(fields.Datetime.now())
                            },
                            "Ack_Exchange": {
                                "Ack_Exchange_INV": "",
                                "Ack_Exchange_INV_AT": ""
                            },
                            "Ack_Exchange_Cons": {
                                "Ack_Exchange_Cons_INV": "",
                                "Ack_Exchange_Cons_INV_AT": ""
                            },
                            "Ack_Send_To_Vendor": {
                                "Ack_Send_To_Vendor_INV": "",
                                "Ack_Send_To_Vendor_INV_AT": ""
                            },
                            "Ack_Verify_Status": {
                                "Ack_Verify_INV": "",
                                "Ack_Verify_INV_AT": ""
                            },
                            "Ack_StatusUpdate_Status": {
                                "Ack_StatusUpdate_INV": "",
                                "Ack_StatusUpdate_INV_AT": ""
                            },
                        },
                    }
                    writer = DatumWriter(schema)
                    bytes_writer = io.BytesIO()
                    encoder = avro.io.BinaryEncoder(bytes_writer)
                    writer.write(log_data, encoder)
                    log_producer.send(bytes_writer.getvalue())
                    log_producer.close()

                    client.close()
            return


#   ----------------------------------------    Refund Handler    ----------------------------------------

async def refund_producer(refund_id):
    successful_refund = False
    refund_line = []
    client = None

    line_sequence_number = 0
    for line in refund_id.invoice_line_ids:
        line_sequence_number = line_sequence_number + 1
        refund_line.append({
            "sno": str(line_sequence_number or ''),
            "hsncode": '',
            "barcode": str(line.product_id.barcode or ''),
            "invoicing_policy": str(line.product_id.product_tmpl_id.invoice_policy or ''),
            "Product_desc": str(line.product_id.product_tmpl_id.description_sale or ''),
            "product_name": str(line.product_id.product_tmpl_id.name or ''),
            "product_type": str(line.product_id.product_tmpl_id.detailed_type or ''),
            "product_category": str(line.product_id.product_tmpl_id.categ_id.name or ''),
            "qty": str(line.quantity or ''),
            "unit": str(line.product_uom_id.name or ''),
            "unit_price": str(line.price_unit or ''),
            "amount_type": str(line.tax_ids.amount_type or ""),
            "tax_type": str(line.tax_ids.type_tax_use or ""),
            "tax_scope": str(line.tax_ids.tax_scope or ""),
            "tax_amount": str(line.tax_ids.amount or ""),
            "Line_allowance_code": '',
            "Line_allowance_reason": '',
            "Line_allowance_amount": '',
            "Line_charge_code": '',
            "Line_charge_reason": '',
            "Line_charge_amount": '',
            "total_price": str(line.price_subtotal or ''),
        })

    refund_data = {
        "Invoice_Reference": {
            "Buy_ref_no": str(refund_id.name or ''),
            "Seller_ref_no": str(refund_id.reversed_entry_id.ref or ''),
            "invoice_declaration": "",
        },
        "Invoice_Desc": {
            "taxschema": str(fields.datetime.now()),
            "InvType": str(refund_id.move_type or ''),
            "Invoice_no": str(refund_id.id or ''),
            "Invoice_ref": str(refund_id.name or ''),
            "Inv_Dt": str(refund_id.invoice_date or ''),
            "payment_due_Dt": str(refund_id.invoice_date_due or ''),
        },
        "Invoice_source_process": {
            "process": "AR",
            "SupType": "B2B",
            "proccess_reference_no": "",
        },
        "Seller": {
            "tin_no": str(refund_id.partner_id.vat or ''),
            "license_number": "",
            "vat_reg_no": "",
            "vat_reg_Dt": '',
            "address": '',
            "company_name": str(refund_id.partner_id.name).replace(' ', '').lower(),
            "user_name": str(refund_id.env.user.name or ''),
        },
        "Buyer": {
            "tin_no": str(refund_id.env.company.vat or ''),
            "vat_reg_no": str(refund_id.env.company.vat or ''),
            "address": str(refund_id.env.company.name or ''),
            "location": str(refund_id.env.company.vat or ''),
            "phone_no": str(refund_id.env.company.phone or ''),
            "email": str(refund_id.env.company.email or ''),
            "company_name": str(refund_id.env.company.name).replace(' ', '').lower(),
        },
        "Invoice_total": str(refund_id.amount_total or ''),
        "Vat_breakdown": {
            "Vat_category_code": "",
            "Vat_reason_code": "",
            "Vat_reason_text": "",
            "Vat_breakdown_amount": str(refund_id.amount_tax or ''),
        },
        "Invoice_allowance": "",
        "Invoice_charge": "",
        "Invoice_line": refund_line,
    }

    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
    finally:
        if client:
            refund_produced = await _refund_mor_producer(refund_id, client, refund_data)
            if refund_produced:
                refund_acknowledged_consumed = await _refund_mor_consumer(refund_id, client)
                successful_refund = bool(refund_acknowledged_consumed)
            client.close()
        return successful_refund

async def _refund_mor_producer(refund_id, client, refund_data):
    refund_avro = RefundSchema.refund_schema
    schema = avro.schema.parse(json.dumps(refund_avro))
    own_producer = None
    mor_producer = None
    log_producer = None
    # refund_produced = False
    try:
        own_producer = client.create_producer(
            "persistent://" + str(refund_id.env.company.name).replace(' ', '').lower() + "/invoice/refund")
        mor_producer = client.create_producer("persistent://mor/invoice/refund")
    except Exception as e:
        _logger.warning("%s:Addis Systems couldn't create producers!", e)
        raise UserError("Addis Systems couldn't create producers!") from e
    finally:
        if own_producer and mor_producer:
            writer = DatumWriter(schema)
            bytes_writer = io.BytesIO()
            encoder = avro.io.BinaryEncoder(bytes_writer)
            writer.write(refund_data, encoder)
            own_producer.send(bytes_writer.getvalue())
            mor_producer.send(bytes_writer.getvalue())

            refund_produced = True

            # Log Tracking Producer

            # log_avro_schema = logSchema.log_tracking_schema
            # log_schema = avro.schema.parse(json.dumps(log_avro_schema))
            #
            # try:
            #     log_producer = client.create_producer("persistent://pulsar/default/LogTracking")
            # except Exception as e:
            #     _logger.warning("%s:Addis Systems couldn't create producers!", e)
            # finally:
            #     if log_producer:
            #         log_data = {
            #             "InvoiceCreatedDate": str(fields.Datetime.now()),
            #             "InvoiceID": str(refund_id.name or None),
            #             "CompanyName": str(refund_id.env.company.name).replace(' ', '').lower(),
            #             "ErrorResponse": "",
            #             "ErrorStatus": {
            #                 "sentStatus": {
            #                     "Sent_INV": "True",
            #                     "Sent_INV_AT": str(fields.Datetime.now())
            #                 },
            #                 "received_Status": {
            #                     "Received_INV": "",
            #                     "Received_INV_AT": ""
            #                 },
            #                 "Ack_gen_Status": {
            #                     "Ack_Gen_INV": "",
            #                     "Ack_Gen_INV_AT": ""
            #                 },
            #                 "Ack_save_Status": {
            #                     "Ack_Save_INV": "",
            #                     "Ack_Save_INV_AT": ""
            #                 },
            #                 "Ack_Sent_Status": {
            #                     "Ack_Sent_INV": "",
            #                     "Ack_Sent_INV_AT": ""
            #                 },
            #                 "Ack_Consume_Status": {
            #                     "Ack_Consume_INV": "",
            #                     "Ack_Consume_INV_AT": ""
            #                 },
            #                 "Ack_Exchange": {
            #                     "Ack_Exchange_INV": "",
            #                     "Ack_Exchange_INV_AT": ""
            #                 },
            #                 "Ack_Exchange_Cons": {
            #                     "Ack_Exchange_Cons_INV": "",
            #                     "Ack_Exchange_Cons_INV_AT": ""
            #                 },
            #                 "Ack_Send_To_Vendor": {
            #                     "Ack_Send_To_Vendor_INV": "",
            #                     "Ack_Send_To_Vendor_INV_AT": ""
            #                 },
            #                 "Ack_Verify_Status": {
            #                     "Ack_Verify_INV": "",
            #                     "Ack_Verify_INV_AT": ""
            #                 },
            #                 "Ack_StatusUpdate_Status": {
            #                     "Ack_StatusUpdate_INV": "",
            #                     "Ack_StatusUpdate_INV_AT": ""
            #                 },
            #             },
            #         }
            #         writer = DatumWriter(log_schema)
            #         bytes_writer = io.BytesIO()
            #         encoder = avro.io.BinaryEncoder(bytes_writer)
            #         writer.write(log_data, encoder)
            #         log_producer.send(bytes_writer.getvalue())

            own_producer.close()
            mor_producer.close()
            # log_producer.close()
    return refund_produced

async def _refund_mor_consumer(refund_id, client):
    consumer = None
    topic_name = "persistent://" + str(refund_id.env.company.name).replace(' ', '').lower() + "/invoice/refundack"
    consumer_conf = {"subscription_name": str(refund_id.env.company.name).replace(' ', '').lower()}

    try:
        consumer = client.subscribe(topic_name, **consumer_conf)
    except Exception:
        _logger.warning("Addis Systems topic subscription couldn't be achieved", topic_name, consumer_conf)
    finally:
        if consumer:
            msg = consumer.receive()
            if isinstance(msg.data(), bytes):
                data_string = msg.data().decode('utf-8')
            else:
                data_string = msg.data()

            datajson = json.loads(data_string)
            is_e_invoice = await check_partner_electronic_invoice_user(refund_id.partner_id)

            refund_id.IRN = datajson['IRN']
            refund_id.acknowledgement_number = datajson['AckNo']
            refund_id.acknowledgement_date = datajson['AckDt']
            refund_id.signed_invoice = datajson['Signed_invoice']
            refund_id.signed_qr_code = datajson['Signed_QRCode']
            refund_id.created_date = datajson['Created_Date']
            refund_id.created_by = datajson['Created_by']
            refund_id.invoice_status = 'registered' if datajson['Inv_Status'] == 'Registered' else 'failed'
            refund_id.partner_e_invoicing = is_e_invoice
            consumer.acknowledge(msg)
            return True

async def refund_log_tracking_producer_consume(refund_id):
    log_avro_schema = logSchema.log_tracking_schema
    schema = avro.schema.parse(json.dumps(log_avro_schema))
    log_producer = None
    client = None
    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
    finally:
        if client:
            try:
                log_producer = client.create_producer("persistent://pulsar/default/LogTracking")
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if log_producer:
                    log_data = {
                        "InvoiceCreatedDate": str(fields.Datetime.now()),
                        "InvoiceID": str(refund_id.name or None),
                        "CompanyName": str(refund_id.env.company.name).replace(' ', '').lower(),
                        "ErrorResponse": "",
                        "ErrorStatus": {
                            "sentStatus": {
                                "Sent_INV": "",
                                "Sent_INV_AT": ""
                            },
                            "received_Status": {
                                "Received_INV": "",
                                "Received_INV_AT": ""
                            },
                            "Ack_gen_Status": {
                                "Ack_Gen_INV": "",
                                "Ack_Gen_INV_AT": ""
                            },
                            "Ack_save_Status": {
                                "Ack_Save_INV": "",
                                "Ack_Save_INV_AT": ""
                            },
                            "Ack_Sent_Status": {
                                "Ack_Sent_INV": "",
                                "Ack_Sent_INV_AT": ""
                            },
                            "Ack_Consume_Status": {
                                "Ack_Consume_INV": "True",
                                "Ack_Consume_INV_AT": str(fields.Datetime.now())
                            },
                            "Ack_Exchange": {
                                "Ack_Exchange_INV": "",
                                "Ack_Exchange_INV_AT": ""
                            },
                            "Ack_Exchange_Cons": {
                                "Ack_Exchange_Cons_INV": "",
                                "Ack_Exchange_Cons_INV_AT": ""
                            },
                            "Ack_Send_To_Vendor": {
                                "Ack_Send_To_Vendor_INV": "",
                                "Ack_Send_To_Vendor_INV_AT": ""
                            },
                            "Ack_Verify_Status": {
                                "Ack_Verify_INV": "",
                                "Ack_Verify_INV_AT": ""
                            },
                            "Ack_StatusUpdate_Status": {
                                "Ack_StatusUpdate_INV": "",
                                "Ack_StatusUpdate_INV_AT": ""
                            },
                        },
                    }
                    writer = DatumWriter(schema)
                    bytes_writer = io.BytesIO()
                    encoder = avro.io.BinaryEncoder(bytes_writer)
                    writer.write(log_data, encoder)
                    log_producer.send(bytes_writer.getvalue())
                    log_producer.close()

                    client.close()
            return

