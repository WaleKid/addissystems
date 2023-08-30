from threading import Thread, enumerate
import logging
import pulsar

import avro.schema
from avro.io import DatumWriter, DatumReader
import io

import json
from odoo.exceptions import UserError
from odoo import api, SUPERUSER_ID
from odoo import _

from ..avro_schema import dispatch_schema

_logger = logging.getLogger(__name__)


def stock_receipt_consumer_asynch(stock_env, thread_name):
    dispatch_avro = dispatch_schema.dispatch_avro
    schema = avro.schema.parse(json.dumps(dispatch_avro))

    def stock_receipt_pulsar_waiter(stock_env):
        consumer = None

        client = pulsar.Client("pulsar://196.189.124.178:6650")
        topic_name = "persistent://" + stock_env.env.company.name.replace(' ', '').lower() + "/orders/receipt"
        consumer_configuration = {"subscription_name": str(stock_env.env.company.name).replace(' ', '').lower()}
        try:
            consumer = client.subscribe(topic_name, **consumer_configuration)
        except Exception as e:
            consumer = None
            _logger.warning("Addis Systems topic subscription couldn't be achieved", e)

        finally:
            if consumer:
                while True:
                    if msg := consumer.receive():
                        bytes_writer = io.BytesIO(msg.data())
                        decoder = avro.io.BinaryDecoder(bytes_writer)
                        datum_reader = avro.io.DatumReader(schema)
                        result = datum_reader.read(decoder)

                        if result and stock_receipt_create(stock_env, result):
                            consumer.acknowledge(msg)

    def stock_receipt_create(stock_env, stock_receipt_data_dic):
        stock_receipt_reference = stock_receipt_data_dic['Dispatch_ref']
        seller_info = stock_receipt_data_dic["Seller"]
        buyer_info = stock_receipt_data_dic['Buyer']
        stock_receipt_dispatch_info = stock_receipt_data_dic['Dispatch_info']
        stock_receipt_delivery_info = stock_receipt_data_dic["Delivery_info"]
        stock_receipt_line = stock_receipt_data_dic["Stock_Move_line"]

        with stock_env.env.registry.cursor() as new_cr:
            env = api.Environment(new_cr, SUPERUSER_ID, {})
            partner_id = env['res.partner'].search(['|', ('name', '=', seller_info['company_name']), ('vat', '=', seller_info['tin_no'])], limit=1)
            if purchase_order_id := env['purchase.order'].search([('name', '=', stock_receipt_reference["Buyer_ref_no"]), ('partner_id', '=', partner_id.id), ('state', 'in', ['purchase', 'done'])], limit=1):
                count_pickings = env['stock.picking'].search_count([('origin', '=', purchase_order_id.name), ('partner_id', '=', partner_id.id), ])
                purchase_order_id.partner_ref = stock_receipt_reference["Seller_order_ref_no"]
                if purchase_default_picking := env['stock.picking'].search([('origin', '=', purchase_order_id.name), ('partner_id', '=', partner_id.id), ('state', 'in', ['assigned', 'waiting', 'confirmed'])], limit=1):

                    to_backorder = False
                    purchase_default_picking.dispatch_reference_number = stock_receipt_reference['Disp_advice_ref_no']

                    for delivery_line in stock_receipt_line:
                        product_tmpl_id = env['product.template'].search([('name', '=', delivery_line["product_name"])], limit=1)
                        product_id = env['product.product'].search([('product_tmpl_id', '=', product_tmpl_id.id)], limit=1)
                        line = purchase_default_picking.move_ids_without_package.search([('product_id', '=', product_id.id), ('state', 'in', ['assigned', 'waiting', 'confirmed'])], limit=1)
                        if line.product_uom_qty >= float(delivery_line["quantity_done"]):
                            line.quantity_done = float(delivery_line["quantity_done"])

                    # Sanity check
                    for line in purchase_default_picking.move_ids_without_package:
                        if line.product_uom_qty > line.quantity_done:
                            to_backorder = True

                bo_confirm = env['stock.backorder.confirmation'].create({'pick_ids': [purchase_default_picking.id]}).with_context(button_validate_picking_ids=[purchase_default_picking.id])

                if to_backorder:
                    bo_confirm.process()
                else:
                    bo_confirm.process_cancel_backorder()

                return True
            elif purchase_order_id := env['purchase.order'].search([('name', '=', "P00001"), ('partner_id', '=', partner_id.id), ('state', 'not in', ['purchase', 'done'])], limit=1):
                print("\nPurchase Order Not Validated Yet")
                return False

    stock_receipt_pulsar_waiter(stock_env)


def stock_delivery_confirmation_consumer_asynch(stock_env, thread_name):
    dispatch_avro = dispatch_schema.dispatch_avro
    schema = avro.schema.parse(json.dumps(dispatch_avro))

    def stock_delivery_confirmation_pulsar_waiter(stock_env):
        consumer = None

        client = pulsar.Client("pulsar://196.189.124.178:6650")
        topic_name = "persistent://" + stock_env.env.company.name.replace(' ', '').lower() + "/orders/delivery"
        consumer_configuration = {"subscription_name": str(stock_env.env.company.name).replace(' ', '').lower()}
        try:
            consumer = client.subscribe(topic_name, **consumer_configuration)
        except Exception as e:
            consumer = None
            _logger.warning("Addis Systems topic subscription couldn't be achieved", e)

        finally:
            if consumer:
                while True:
                    if msg := consumer.receive():
                        bytes_writer = io.BytesIO(msg.data())
                        decoder = avro.io.BinaryDecoder(bytes_writer)
                        datum_reader = avro.io.DatumReader(schema)
                        result = datum_reader.read(decoder)

                        if result and stock_delivery_confirm_create(stock_env, result):
                            consumer.acknowledge(msg)

    def stock_delivery_confirm_create(stock_env, stock_receipt_data_dic):
        stock_receipt_reference = stock_receipt_data_dic['Dispatch_ref']
        seller_info = stock_receipt_data_dic["Seller"]
        buyer_info = stock_receipt_data_dic['Buyer']
        stock_receipt_dispatch_info = stock_receipt_data_dic['Dispatch_info']
        stock_receipt_delivery_info = stock_receipt_data_dic["Delivery_info"]
        stock_receipt_line = stock_receipt_data_dic["Stock_Move_line"]

        with stock_env.env.registry.cursor() as new_cr:
            env = api.Environment(new_cr, SUPERUSER_ID, {})
            partner_id = env['res.partner'].search(['|', ('name', '=', seller_info['company_name']), ('vat', '=', seller_info['tin_no'])], limit=1)

            if sales_order_id := env['sale.order'].search([('client_order_ref', '=', stock_receipt_reference["Seller_order_ref_no"]), ('partner_id', '=', partner_id.id), ('state', 'in', ['sale', 'done'])], limit=1):
                count_pickings = env['stock.picking'].search_count([('origin', '=', sales_order_id.name), ('partner_id', '=', partner_id.id), ])
                if confirmed_picking := env['stock.picking'].search(
                        [('dispatch_reference_number', '=', stock_receipt_reference['Disp_advice_ref_no']), ('origin', '=', sales_order_id.name), ('partner_id', '=', partner_id.id), ('state', 'in', ['on_delivery'])], limit=1):
                    confirmed_picking.state = 'done'
                    return True

    stock_delivery_confirmation_pulsar_waiter(stock_env)
