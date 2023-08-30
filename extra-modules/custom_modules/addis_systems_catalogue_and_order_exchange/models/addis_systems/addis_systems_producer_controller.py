import pulsar
import json
import logging
import avro.schema
from avro.io import DatumWriter
import io

from ..avro_schema import ReqestForCatalogue
from ..avro_schema import CatalogueQuotations
from ..avro_schema import PurchaseOrder
from ..avro_schema import SalesOrder

_logger = logging.getLogger(__name__)


def general_producer(schema, data, producer):
    writer = DatumWriter(schema)
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(data, encoder)
    producer.send(bytes_writer.getvalue())
    return True


def send_request_for_catalogue_order(rfc_id, partner):
    client = None
    producer = None
    rfc_produced = False

    rfc_avro = ReqestForCatalogue.rfc_schema
    rfc_schema = avro.schema.parse(json.dumps(rfc_avro))

    rfc_data = {
        "Request_For_Catalogue_Ref": {
            "RFC_Reference": str(rfc_id.name),
            "pass_to_prospective_customer": str(rfc_id.pass_to_prospective_customer),
            "with_Price": str(rfc_id.catalogue_with_price)
        },
        "Request_For_Catalogue_Desc": {
            "Date": str(rfc_id.requested_date),
            "Expected_Date": str(rfc_id.expire_date),
            "Descriptive_Literature": str(rfc_id.descriptive_literature),
            "Condition": str(rfc_id.condition),
            "trade_terms": str(rfc_id.trade_terms)
        },
        "Seller": {
            "tin_no": str(partner.vat),
            "licence_number": "",
            "vat_reg_no": "",
            "vat_reg_Dt": "",
            "company_name": str(partner.name)
        },
        "Buyer": {
            "tin_no": str(rfc_id.company_id.vat),
            "vat_reg_no": "",
            "address": str(rfc_id.company_id.state_id),
            "location": str(rfc_id.company_id.company_details),
            "phone_no": str(rfc_id.company_id.phone),
            "email": str(rfc_id.company_id.email),
            "buyer_name": str(rfc_id.company_id.name)
        }
    }

    print(rfc_data)

    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        _logger.warning("%s:Connection to Addis Systems could not be achieved. please try later!", e)
    finally:
        if client:
            try:
                topic = 'persistent://' + str(partner.name).replace(' ', '').lower() + '/catalogue/rfc'
                producer = client.create_producer(topic)
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if producer:
                    rfc_produced = general_producer(rfc_schema, rfc_data, producer)
                    producer.close()
                client.close()

    return rfc_produced


def send_catalogue_quotation(catalogue_quotation):
    client = None
    producer = None
    quotation_produced = False

    catalogue_quotation_avro = CatalogueQuotations.catalogue_quotation_schema
    catalogue_quotation_schema = avro.schema.parse(json.dumps(catalogue_quotation_avro))

    catalogue_quotation_products = []

    for product in catalogue_quotation.catalogue_quotation_line:
        product_template = product.product_id.product_tmpl_id
        products_line = {
            "Product_Name": str(product.product_id.name),
            "Product_UoM": str(product.product_id.uom_id.name or None),
            "Product_Type": str(product.product_type),
            "Product_Price": str(product.product_price) if product.with_price else "0",
            "Product_Default_Code": str(product.default_code or None),
            "Product_Barcode": str(product.product_id.barcode or None),
            "Product_Weight": str(product.weight),
            "Product_Volume": str(product.volume),
            "Product_Lead_Time": str(product.lead_time),
            "Product_With_Variant": "",
            "Product_Variants_Desc": "",
        }
        catalogue_quotation_products += [products_line]

    catalogue_quotation_data = {
        "Catalogue_Quotation_Ref": {
            "Catalogue_Request_Reference": str(catalogue_quotation.name),
            "Catalogue_Quotation_Reference": str(catalogue_quotation.pass_to_prospective_customer),
            "RFC_Reference": str(catalogue_quotation.partner_rfc_reference)
        },
        "Catalogue_Products": catalogue_quotation_products,
        "Seller": {
            "tin_no": str(catalogue_quotation.company_id.vat),
            "licence_number": "",
            "vat_reg_no": "",
            "vat_reg_Dt": "",
            "company_name": str(catalogue_quotation.company_id.name)
        },
        "Buyer": {
            "tin_no": str(catalogue_quotation.partner_id.vat),
            "vat_reg_no": "",
            "address": str(catalogue_quotation.partner_id.state_id),
            "location": "",
            "phone_no": str(catalogue_quotation.partner_id.phone),
            "email": str(catalogue_quotation.partner_id.email),
            "buyer_name": str(catalogue_quotation.partner_id.name)
        }
    }

    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        _logger.warning("%s:Connection to Addis Systems could not be achieved. please try later!", e)
    finally:
        if client:
            try:
                topic = 'persistent://' + str(catalogue_quotation.partner_id.name).replace(' ', '').lower() + '/catalogue/catalogue'
                producer = client.create_producer(topic)
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if producer:
                    quotation_produced = general_producer(catalogue_quotation_schema, catalogue_quotation_data, producer)
                    producer.close()
                client.close()
    return quotation_produced


def send_purchase_quotation_price_request(purchase_order_id):
    client = None
    producer = None
    po_quotation_produced = False

    po_quotation_avro = PurchaseOrder.purchase_order_schema
    po_quotation_schema = avro.schema.parse(json.dumps(po_quotation_avro))

    po_order_line = []

    line_sequence_number = 0
    for po_line in purchase_order_id.order_line:
        line_sequence_number = line_sequence_number + 1
        po_order_line.append(
            {
                "sno": '',
                "hsncode": "",
                "item_name": str(po_line.product_id.product_tmpl_id.name),
                "qty": str(po_line.product_qty),
                "unit": str(po_line.product_uom.name),
                "price": str(po_line.price_unit),
                "tax": "",
                "Line_charge_code": "",
                "Line_charge_reason": "",
                "Line_charge_amount": "",
                "total_price": ""
            }
        )

    purchase_order_data = {
        "Purchase_Order_ref": {
            "PO_ref_no": str(purchase_order_id.name),
            "RFQ_ref_no": str(purchase_order_id.name),
            "Rec_advice_ref_no": "",
            "PO_State": str(purchase_order_id.state),
            "CAT_Reference": str(purchase_order_id.catalogue_id.partner_reference)
        },
        "Purchase_Order_Desc": {
            "PO_exchange": purchase_order_id.state,
            "Purchase_Order_Type": "",
            "PO_no": "",
            "Receipt_Dt": str(purchase_order_id.date_planned),
            "Order_deadline": str(purchase_order_id.date_order)
        },
        "Seller": {
            "tin_no": str(purchase_order_id.partner_id.vat),
            "licence_number": "",
            "vat_reg_no": "",
            "vat_reg_Dt": "",
            "company_name": str(purchase_order_id.partner_id.name)
        },
        "Buyer": {
            "tin_no": str(purchase_order_id.company_id.vat),
            "vat_reg_no": "",
            "address": str(purchase_order_id.company_id.state_id),
            "location": str(purchase_order_id.company_id.company_details),
            "phone_no": str(purchase_order_id.company_id.phone),
            "email": str(purchase_order_id.company_id.email),
            "buyer_name": str(purchase_order_id.company_id.name)
        },
        "Delivery_info": {
            "Delivery_note_number": "",
            "delivery_date": "",
            "delivery_location": "",
            "delivery_address": ""
        },
        "Purchase_total": str(purchase_order_id.amount_total),
        "Vat_breakdown": {
            "Vat_category_code": "",
            "Vat_reason_code": "",
            "Vat_reason_text": "",
            "Vat_breakdown_amount": ""
        },
        "Purchase_line": po_order_line
    }

    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        _logger.warning("%s:Connection to Addis Systems could not be achieved. please try later!", e)
    finally:
        if client:
            try:
                topic = 'persistent://' + str(purchase_order_id.partner_id.name).replace(' ', '').lower() + '/orders/salesOrder'
                producer = client.create_producer(topic)
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if producer:
                    po_quotation_produced = general_producer(po_quotation_schema, purchase_order_data, producer)
                client.close()

    return po_quotation_produced


def send_rfq_update_for_buyer(sales_order_rfq):
    client = None
    producer = None
    so_produced = False

    so_quotation_avro = SalesOrder.sales_order_schema
    so_quotation_schema = avro.schema.parse(json.dumps(so_quotation_avro))

    so_order_line = []

    line_sequence_number = 0
    for so_line in sales_order_rfq.order_line:
        line_sequence_number = line_sequence_number + 1
        so_order_line.append(
            {
                "sno": '',
                "hsncode": "",
                "item_name": str(so_line.product_id.product_tmpl_id.name),
                "qty": str(so_line.product_uom_qty),
                "unit": str(so_line.product_uom.name),
                "price": str(so_line.price_unit),
                "tax": "",
                "Line_charge_code": "",
                "Line_charge_reason": "",
                "Line_charge_amount": "",
                "total_price": ""
            }
        )

    sales_order_data = {
        "Sales_Order_ref": {
            "SO_ref_no": str(sales_order_rfq.name),
            "RFQ_ref_no": str(sales_order_rfq.name),
            "Rec_advice_ref_no": "",
            "PO_State": str(sales_order_rfq.state),
        },
        "Sales_Order_Desc": {
            "SO_exchange": 'update' if sales_order_rfq.client_order_ref else 'new',
            "Customer_Order_Ref": sales_order_rfq.client_order_ref or None,
            "Sales_Order_Type": "",
            "SO_no": "",
            "Receipt_Dt": str(sales_order_rfq.date_order),
            "Order_deadline": str(sales_order_rfq.validity_date)
        },
        "Seller": {
            "tin_no": str(sales_order_rfq.company_id.vat),
            "licence_number": "",
            "vat_reg_no": "",
            "vat_reg_Dt": "",
            "company_name": str(sales_order_rfq.company_id.name)
        },
        "Buyer": {
            "tin_no": str(sales_order_rfq.partner_id.vat),
            "vat_reg_no": "",
            "address": str(sales_order_rfq.partner_id.state_id),
            "location": '',
            "phone_no": str(sales_order_rfq.partner_id.phone),
            "email": str(sales_order_rfq.partner_id.email),
            "buyer_name": str(sales_order_rfq.partner_id.name)
        },
        "Delivery_info": {
            "Delivery_note_number": "",
            "delivery_date": "",
            "delivery_location": "",
            "delivery_address": ""
        },
        "Sales_total": str(sales_order_rfq.amount_total),
        "Vat_breakdown": {
            "Vat_category_code": "",
            "Vat_reason_code": "",
            "Vat_reason_text": "",
            "Vat_breakdown_amount": ""
        },
        "Order_line": so_order_line
    }

    try:
        client = pulsar.Client("pulsar://196.189.124.178:6650")
    except Exception as e:
        _logger.warning("%s:Connection to Addis Systems could not be achieved. please try later!", e)
        # raise UserError(f"Connection to Addis Systems could not be achieved. please try later!") from e
    finally:
        if client:
            try:
                topic = 'persistent://' + str(sales_order_rfq.partner_id.name).replace(' ', '').lower() + '/orders/Quotations'
                producer = client.create_producer(topic)
            except Exception as e:
                _logger.warning("%s:Addis Systems couldn't create producers!", e)
            finally:
                if producer:
                    so_produced = general_producer(so_quotation_schema, sales_order_data, producer)
                    producer.close()
                client.close()

    return so_produced


def send_sales_order_for_vendor(sales_order):
    print(sales_order)
