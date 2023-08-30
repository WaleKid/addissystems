from odoo.tools.safe_eval import json
from odoo.exceptions import UserError

import avro.schema
from avro.io import DatumWriter
import io

import pulsar

import logging

from ..avro_schema import provision_dispatch_schema

_logger = logging.getLogger(__name__)


async def dispatch_producer(self, stock_picking_id):
    dispatch_avro = provision_dispatch_schema.provision_dispatch_avro
    schema = avro.schema.parse(json.dumps(dispatch_avro))
    stock_move_line = []
    client = None

    line_sequence_number = 0
    for line in stock_picking_id.move_ids_without_package:
        line_sequence_number = line_sequence_number + 1
        stock_move_line.append({
            "sno": str(line_sequence_number),
            "item_name": str(line.product_id.product_tmpl_id.name),
            "qty": str(line.quantity_done),
            "unit": str(line.product_id.product_tmpl_id.uom_id.name),
            "price": "",
        })

    dispatch_json = {
        "Dispatch_ref": {
            "Buy_ref_no": "",
            "Contrat_ref_no": "",
            "Seller_order_ref_no": "",
            "Rec_advice_ref_no": "",
            "Dispatch_ref": "",
            "Disp_advice_ref_no": "",
            "Tender_ref_no": ""
        },
        "Buyer": {
            "address": str(stock_picking_id.partner_id.country_id.name or ""),
            "buyer_name": str(stock_picking_id.partner_id.name or ""),
            "email": str(stock_picking_id.partner_id.email or ""),
            "location": str(stock_picking_id.partner_id.state_id.name or ""),
            "phone_no": str(stock_picking_id.partner_id.phone or ""),
            "tin_no": str(stock_picking_id.partner_id.vat or ""),
            "vat_reg_no": str(stock_picking_id.partner_id.vat or "")
        },
        "Dispatch_info": {
            "Dispatch_number": str(stock_picking_id.name or ""),
            "Dispatch_date": str(stock_picking_id.name or ""),
            "Dispatch_location": str(stock_picking_id.name or ""),
            "Dispatch_note_number": str(stock_picking_id.name or "")
        },
        "Delivery_info": {
            "Delivery_address": "",
            "Delivery_date": str(stock_picking_id.date_deadline or ""),
            "Delivery_location": "",
            "Delivery_note_number": str(stock_picking_id.name or "")
        },
        "Dispatch_line": stock_move_line
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
                producer = client.create_producer("persistent://addissystems/orders/provision")
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if producer:
                    writer = DatumWriter(schema)
                    bytes_writer = io.BytesIO()
                    encoder = avro.io.BinaryEncoder(bytes_writer)
                    writer.write(dispatch_json, encoder)
                    producer.send(bytes_writer.getvalue())

                    producer.close()
            client.close()

    return
