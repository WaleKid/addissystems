from odoo.tools.safe_eval import json
from odoo.exceptions import UserError
from odoo import fields

import avro.schema
from avro.io import DatumWriter
import io

import pulsar
import logging

from ..avro_schema import dispatch_schema

_logger = logging.getLogger(__name__)


async def dispatch_producer(inventory_id, origin):
    dispatch_produced = False
    dispatch_avro = dispatch_schema.dispatch_avro
    schema = avro.schema.parse(json.dumps(dispatch_avro))
    stock_move_line = []
    client = None

    line_sequence_number = 0
    for line in inventory_id.move_ids_without_package:
        line_sequence_number = line_sequence_number + 1
        stock_move_line.append({
            "sno": str(line_sequence_number),
            "product_name": str(line.product_id.product_tmpl_id.name),
            "product_UoM": str(line.product_uom.name),
            "product_qty": str(line.product_qty),
            "product_UoM_quantity": str(line.product_uom_qty),
            "quantity_done": str(line.quantity_done),
            "hsncode": "",
        })

    dispatch_json = {
        "Dispatch_ref": {
            "Buyer_ref_no": str(origin.client_order_ref or ""),
            "Contrat_ref_no": "",
            "Seller_order_ref_no": str(origin.name or ""),
            "Rec_advice_ref_no": "",
            "Dispatch_ref": str(inventory_id.name or ""),
            "Disp_advice_ref_no": str(inventory_id.dispatch_reference_number or ""),
            "Tender_ref_no": ""
        },
        "Seller": {
            "company_name": str(inventory_id.company_id.vat if inventory_id.company_id else ""),
            "licence_number": str(inventory_id.company_id.vat if inventory_id.company_id else ""),
            "tin_no": str(inventory_id.company_id.vat if inventory_id.company_id else ""),
            "vat_reg_Dt": "",
            "vat_reg_no": ""
        },
        "Buyer": {
            "address": str(inventory_id.partner_id.country_id.name or ""),
            "buyer_name": str(inventory_id.partner_id.name or ""),
            "email": str(inventory_id.partner_id.email or ""),
            "location": str(inventory_id.partner_id.state_id.name or ""),
            "phone_no": str(inventory_id.partner_id.phone or ""),
            "tin_no": str(inventory_id.partner_id.vat or ""),
            "vat_reg_no": str(inventory_id.partner_id.vat or "")
        },
        "Dispatch_info": {
            "Dispatch_number": str(inventory_id.dispatch_reference_number or ""),
            "Dispatch_date": str(fields.Datetime.now()),
            "Dispatch_location": "",
            "Dispatch_note_number": str(inventory_id.name or ""),
            "Backorder": ""
        },
        "Delivery_info": {
            "Delivery_address": str(inventory_id.partner_id.state_id.name or ""),
            "Delivery_date": str(inventory_id.date_done or ""),
            "Delivery_location": str(inventory_id.partner_id.city or ""),
            "Delivery_note_number": str(inventory_id.name or "")
        },
        "Stock_Move_line": stock_move_line
    }

    producer = None
    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        _logger.warning("%s:Connection to Addis Systems could not be achieved. please try later!", e)
        raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
    finally:
        if client:
            try:
                producer = client.create_producer("persistent://" + str(inventory_id.partner_id.name).replace(' ', '').lower() + "/orders/receipt")
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if producer:
                    writer = DatumWriter(schema)
                    bytes_writer = io.BytesIO()
                    encoder = avro.io.BinaryEncoder(bytes_writer)
                    writer.write(dispatch_json, encoder)
                    producer.send(bytes_writer.getvalue())

                    dispatch_produced = True

                    producer.close()
            client.close()

            return dispatch_produced


async def dispatch_receipt_confirm_producer(inventory_id, origin):
    dispatch_produced = False
    dispatch_avro = dispatch_schema.dispatch_avro
    schema = avro.schema.parse(json.dumps(dispatch_avro))
    stock_move_line = []
    client = None

    line_sequence_number = 0
    for line in inventory_id.move_ids_without_package:
        line_sequence_number = line_sequence_number + 1
        stock_move_line.append({
            "sno": str(line_sequence_number),
            "product_name": str(line.product_id.product_tmpl_id.name),
            "product_UoM": str(line.product_uom.name),
            "product_qty": str(line.product_qty),
            "product_UoM_quantity": str(line.product_uom_qty),
            "quantity_done": str(line.quantity_done),
            "hsncode": "",
        })

    dispatch_json = {
        "Dispatch_ref": {
            "Buyer_ref_no": str(origin.name or ""),
            "Contrat_ref_no": "",
            "Seller_order_ref_no": str(inventory_id.origin or ""),
            "Rec_advice_ref_no": "",
            "Dispatch_ref": str(inventory_id.name or ""),
            "Disp_advice_ref_no": str(inventory_id.dispatch_reference_number or ""),
            "Tender_ref_no": ""
        },
        "Seller": {
            "company_name": str(inventory_id.company_id.vat if inventory_id.company_id else ""),
            "licence_number": str(inventory_id.company_id.vat if inventory_id.company_id else ""),
            "tin_no": str(inventory_id.company_id.vat if inventory_id.company_id else ""),
            "vat_reg_Dt": "",
            "vat_reg_no": ""
        },
        "Buyer": {
            "address": str(inventory_id.partner_id.country_id.name or ""),
            "buyer_name": str(inventory_id.partner_id.name or ""),
            "email": str(inventory_id.partner_id.email or ""),
            "location": str(inventory_id.partner_id.state_id.name or ""),
            "phone_no": str(inventory_id.partner_id.phone or ""),
            "tin_no": str(inventory_id.partner_id.vat or ""),
            "vat_reg_no": str(inventory_id.partner_id.vat or "")
        },
        "Dispatch_info": {
            "Dispatch_number": str(inventory_id.dispatch_reference_number or ""),
            "Dispatch_date": str(fields.Datetime.now()),
            "Dispatch_location": "",
            "Dispatch_note_number": str(inventory_id.name or ""),
            "Backorder": ""
        },
        "Delivery_info": {
            "Delivery_address": str(inventory_id.partner_id.state_id.name or ""),
            "Delivery_date": str(inventory_id.date_done or ""),
            "Delivery_location": str(inventory_id.partner_id.city or ""),
            "Delivery_note_number": str(inventory_id.name or "")
        },
        "Stock_Move_line": stock_move_line
    }

    producer = None
    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        _logger.warning("%s:Connection to Addis Systems could not be achieved. please try later!", e)
        raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
    finally:
        if client:
            try:
                producer = client.create_producer("persistent://" + str(inventory_id.partner_id.name).replace(' ', '').lower() + "/orders/delivery")
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if producer:
                    writer = DatumWriter(schema)
                    bytes_writer = io.BytesIO()
                    encoder = avro.io.BinaryEncoder(bytes_writer)
                    writer.write(dispatch_json, encoder)
                    producer.send(bytes_writer.getvalue())

                    dispatch_produced = True

                    producer.close()
            client.close()

            return dispatch_produced
