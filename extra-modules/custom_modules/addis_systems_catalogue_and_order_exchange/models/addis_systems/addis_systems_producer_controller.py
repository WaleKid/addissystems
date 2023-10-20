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


# ---------------------------------------------------------------- Catalogue Exchange Producers ----------------------------------------------------------------
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
            "with_Price": str(rfc_id.catalogue_with_price),
        },
        "Request_For_Catalogue_Desc": {
            "Date": str(rfc_id.requested_date),
            "Expected_Date": str(rfc_id.expire_date),
            "Descriptive_Literature": str(rfc_id.descriptive_literature),
            "Condition": str(rfc_id.condition),
            "trade_terms": str(rfc_id.trade_terms),
        },
        "Seller": {
            "tin_no": str(partner.vat),
            "vat_reg_no": str(partner.company_registry),
            "address": str(f'{partner.country_id.name},{partner.state_id.name},{partner.city},{partner.street2},{partner.street}'),
            "location": str(f"{partner.partner_latitude},{partner.partner_longitude}"),
            "phone_no": str(partner.phone),
            "email": str(partner.email),
            "company_name": str(partner.name),
        },
        "Buyer": {
            "tin_no": str(rfc_id.company_id.vat),
            "vat_reg_no": str(rfc_id.company_id.company_registry),
            "address": str(f'{rfc_id.company_id.country_id.name},{rfc_id.company_id.state_id.name},{rfc_id.company_id.city},{rfc_id.company_id.street2},{rfc_id.company_id.street}'),
            "location": str(f"{rfc_id.company_id.partner_id.partner_latitude},{rfc_id.company_id.partner_id.partner_longitude}"),
            "phone_no": str(rfc_id.company_id.phone),
            "email": str(rfc_id.company_id.email),
            "buyer_name": str(rfc_id.company_id.name),
        },
    }

    try:
        client = pulsar.Client("pulsar://127.0.0.1:6650")
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
            "RFC_Reference": str(catalogue_quotation.partner_rfc_reference),
            "Date_Start": str(catalogue_quotation.start_date),
            "Date_End": str(catalogue_quotation.date_end),
            "INCOTERM": str(catalogue_quotation.incoterm_id.name)
        },
        "Catalogue_Products": catalogue_quotation_products,
        "Seller": {
            "tin_no": str(catalogue_quotation.company_id.vat),
            "vat_reg_no": str(catalogue_quotation.company_id.company_registry),
            "address": str(f'{catalogue_quotation.company_id.country_id.name},{catalogue_quotation.company_id.state_id.name},{catalogue_quotation.company_id.city},{catalogue_quotation.company_id.street2},{catalogue_quotation.company_id.street}'),
            "location": str(f"{catalogue_quotation.company_id.partner_id.partner_latitude},{catalogue_quotation.company_id.partner_id.partner_longitude}"),
            "phone_no": str(catalogue_quotation.company_id.phone),
            "email": str(catalogue_quotation.company_id.email),
            "company_name": str(catalogue_quotation.company_id.name)
        },
        "Buyer": {
            "tin_no": str(catalogue_quotation.partner_id.vat),
            "vat_reg_no": str(catalogue_quotation.partner_id.company_registry),
            "address": str(f'{catalogue_quotation.partner_id.country_id.name},{catalogue_quotation.partner_id.state_id.name},{catalogue_quotation.partner_id.city},{catalogue_quotation.partner_id.street2},{catalogue_quotation.partner_id.street}'),
            "location": str(f"{catalogue_quotation.partner_id.partner_latitude},{catalogue_quotation.partner_id.partner_longitude}"),
            "phone_no": str(catalogue_quotation.partner_id.phone),
            "email": str(catalogue_quotation.partner_id.email),
            "buyer_name": str(catalogue_quotation.partner_id.name)
        }
    }

    try:
        client = pulsar.Client("pulsar://127.0.0.1:6650")
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


# ---------------------------------------------------------------- Sales & Purchase Exchange Producers ----------------------------------------------------------------
def send_po_price_request(purchase_order_id):
    # Purchase Order Price Request Producer
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
                "sequence": '',
                "HSNcode": "",
                "Product_Name": str(po_line.product_id.product_tmpl_id.name),
                "Product_Description": str(),
                "Product_qty": str(po_line.product_qty),
                "Product_unit": str(po_line.product_uom.name),
                "Product_price": str(po_line.price_unit),
                # Tax Related
                "tax_type": str(po_line.taxes_id.type_tax_use if po_line.taxes_id else ""),
                "tax_amount_type": str(po_line.taxes_id.amount_type if po_line.taxes_id else ""),
                "tax_scope": str(po_line.taxes_id.tax_scope if po_line.taxes_id else ""),
                "tax_amount": str(po_line.taxes_id.amount if po_line.taxes_id else ""),
                # Extra
                "Line_charge_code": "",
                "Line_charge_reason": "",
                "Line_charge_amount": "",
                # Total
                "Total_Price": ""
            }
        )

    purchase_order_data = {
        "Purchase_Order_ref": {
            "PO_ref_no": str(purchase_order_id.name),
            "RFC_rfc_no": str(purchase_order_id.rfc_id.name),
            "CAT_ref_no": str(purchase_order_id.catalogue_id.partner_reference),
            "Rec_advice_ref_no": "",
            "PO_status": str(purchase_order_id.state),
        },
        "Purchase_Order_Desc": {
            "Exchange_Title": 'price_request',
            "Purchase_Order_Type": purchase_order_id.po_type,
            "Order_date": str(purchase_order_id.date_order),
            "Planned_Receipt": str(purchase_order_id.date_planned)
        },
        "Seller": {
            "tin_no": str(purchase_order_id.partner_id.vat),
            "vat_reg_no": str(purchase_order_id.partner_id.company_registry),
            "address": str(f'{purchase_order_id.partner_id.country_id.name},{purchase_order_id.partner_id.state_id.name},{purchase_order_id.partner_id.city},{purchase_order_id.partner_id.street2},{purchase_order_id.partner_id.street}'),
            "location": str(f"{purchase_order_id.partner_id.partner_latitude},{purchase_order_id.partner_id.partner_longitude}"),
            "phone_no": str(purchase_order_id.partner_id.phone),
            "email": str(purchase_order_id.partner_id.email),
            "company_name": str(purchase_order_id.partner_id.name)
        },
        "Buyer": {
            "tin_no": str(purchase_order_id.company_id.vat),
            "vat_reg_no": str(purchase_order_id.company_id.company_registry),
            "address": str(f'{purchase_order_id.company_id.country_id.name},{purchase_order_id.company_id.state_id.name},{purchase_order_id.company_id.city},{purchase_order_id.company_id.street2},{purchase_order_id.company_id.street}'),
            "location": str(f"{purchase_order_id.company_id.partner_id.partner_latitude},{purchase_order_id.company_id.partner_id.partner_longitude}"),
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
        client = pulsar.Client("pulsar://127.0.0.1:6650")
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


def send_price_update_buyer(sales_order_rfq):
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
                "sequence": '',
                "HSNcode": "",
                "Product_Name": str(so_line.product_id.product_tmpl_id.name),
                "Product_Description": str(),
                "Product_qty": str(so_line.product_uom_qty),
                "Product_unit": str(so_line.product_uom.name),
                "Product_price": str(so_line.price_unit),
                # Tax Related
                "tax_type": str(so_line.tax_id.type_tax_use if so_line.tax_id else ""),
                "tax_amount_type": str(so_line.tax_id.amount_type if so_line.tax_id else ""),
                "tax_scope": str(so_line.tax_id.tax_scope if so_line.tax_id else ""),
                "tax_amount": str(so_line.tax_id.amount if so_line.tax_id else ""),
                # Extra
                "Line_charge_code": "",
                "Line_charge_reason": "",
                "Line_charge_amount": "",
                # Total
                "Total_Price": ""
            }
        )

    sales_order_data = {
        "Sales_Order_ref": {
            "SO_ref_no": str(sales_order_rfq.name),
            "Customer_PO_ref_no": str(sales_order_rfq.client_order_ref),
            "CAT_ref_no": str(sales_order_rfq.catalogue_quotation_id.name),
            "Rec_advice_ref_no": "",
            "SO_State": str(sales_order_rfq.state),
        },
        "Sales_Order_Desc": {
            "Exchange_Title": 'price_update',
            "Sales_Order_Type": "",
            "SO_no": str(sales_order_rfq.name),
            "Receipt_Dt": str(sales_order_rfq.date_order),
            "Order_deadline": str(sales_order_rfq.validity_date)
        },
        "Seller": {
            "tin_no": str(sales_order_rfq.company_id.vat),
            "vat_reg_no": str(sales_order_rfq.company_id.company_registry),
            "address": str(f'{sales_order_rfq.company_id.country_id.name},{sales_order_rfq.company_id.state_id.name},{sales_order_rfq.company_id.city},{sales_order_rfq.company_id.street2},{sales_order_rfq.company_id.street}'),
            "location": str(f"{sales_order_rfq.company_id.partner_id.partner_latitude},{sales_order_rfq.company_id.partner_id.partner_longitude}"),
            "phone_no": str(sales_order_rfq.company_id.phone),
            "email": str(sales_order_rfq.company_id.email),
            "company_name": str(sales_order_rfq.company_id.name)
        },
        "Buyer": {
            "tin_no": str(sales_order_rfq.partner_id.vat),
            "vat_reg_no": str(sales_order_rfq.partner_id.company_registry),
            "address": str(f'{sales_order_rfq.partner_id.country_id.name},{sales_order_rfq.partner_id.state_id.name},{sales_order_rfq.partner_id.city},{sales_order_rfq.partner_id.street2},{sales_order_rfq.partner_id.street}'),
            "location": str(f"{sales_order_rfq.partner_id.partner_latitude},{sales_order_rfq.partner_id.partner_longitude}"),
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
        client = pulsar.Client("pulsar://127.0.0.1:6650")
    except Exception as e:
        _logger.warning("%s:Connection to Addis Systems could not be achieved. please try later!", e)
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


def send_new_po_request(purchase_order_id):
    # Purchase Order Price Request Producer
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
                "sequence": '',
                "HSNcode": "",
                "Product_Name": str(po_line.product_id.product_tmpl_id.name),
                "Product_Description": str(),
                "Product_qty": str(po_line.product_qty),
                "Product_unit": str(po_line.product_uom.name),
                "Product_price": str(po_line.price_unit),
                # Tax Related
                "tax_type": str(po_line.taxes_id.type_tax_use if po_line.taxes_id else ""),
                "tax_amount_type": str(po_line.taxes_id.amount_type if po_line.taxes_id else ""),
                "tax_scope": str(po_line.taxes_id.tax_scope if po_line.taxes_id else ""),
                "tax_amount": str(po_line.taxes_id.amount if po_line.taxes_id else ""),
                # Extra
                "Line_charge_code": "",
                "Line_charge_reason": "",
                "Line_charge_amount": "",
                # Total
                "Total_Price": ""
            }
        )

    purchase_order_data = {
        "Purchase_Order_ref": {
            "PO_ref_no": str(purchase_order_id.name),
            "RFC_rfc_no": str(purchase_order_id.rfc_id.name),
            "CAT_ref_no": str(purchase_order_id.catalogue_id.partner_reference),
            "Rec_advice_ref_no": "",
            "PO_status": str(purchase_order_id.state),
        },
        "Purchase_Order_Desc": {
            "Exchange_Title": 'new_po',
            "Purchase_Order_Type": purchase_order_id.po_type,
            "Order_date": str(purchase_order_id.date_order),
            "Planned_Receipt": str(purchase_order_id.date_planned)
        },
        "Seller": {
            "tin_no": str(purchase_order_id.partner_id.vat),
            "vat_reg_no": str(purchase_order_id.partner_id.company_registry),
            "address": str(f'{purchase_order_id.partner_id.country_id.name},{purchase_order_id.partner_id.state_id.name},{purchase_order_id.partner_id.city},{purchase_order_id.partner_id.street2},{purchase_order_id.partner_id.street}'),
            "location": str(f"{purchase_order_id.partner_id.partner_latitude},{purchase_order_id.partner_id.partner_longitude}"),
            "phone_no": str(purchase_order_id.partner_id.phone),
            "email": str(purchase_order_id.partner_id.email),
            "company_name": str(purchase_order_id.partner_id.name)
        },
        "Buyer": {
            "tin_no": str(purchase_order_id.company_id.vat),
            "vat_reg_no": str(purchase_order_id.company_id.company_registry),
            "address": str(f'{purchase_order_id.company_id.country_id.name},{purchase_order_id.company_id.state_id.name},{purchase_order_id.company_id.city},{purchase_order_id.company_id.street2},{purchase_order_id.company_id.street}'),
            "location": str(f"{purchase_order_id.company_id.partner_id.partner_latitude},{purchase_order_id.company_id.partner_id.partner_longitude}"),
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
        client = pulsar.Client("pulsar://127.0.0.1:6650")
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


def send_sales_order_for_vendor(sales_order):
    print(sales_order)
