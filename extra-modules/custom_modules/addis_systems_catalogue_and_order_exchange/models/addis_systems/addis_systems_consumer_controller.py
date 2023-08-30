import logging
import pulsar
import io
import avro.schema

from odoo.tools.safe_eval import json
from odoo.exceptions import UserError
from odoo import api, SUPERUSER_ID
from odoo import _

from ..avro_schema import ReqestForCatalogue
from ..avro_schema import CatalogueQuotations
from ..avro_schema import PurchaseOrder
from ..avro_schema import SalesOrder

_logger = logging.getLogger(__name__)


def request_for_catalogue_consumer_asynch(request_for_catalogue_env):
    rfc_avro = ReqestForCatalogue.rfc_schema
    schema = avro.schema.parse(json.dumps(rfc_avro))

    def request_for_catalogue_pulsar_waiter(rfc_env):
        consumer = None

        client = pulsar.Client("pulsar://196.189.124.178:6650")
        topic_name = "persistent://" + rfc_env.env.company.name.replace(' ', '').lower() + "/catalogue/rfc"
        consumer_configuration = {"subscription_name": str(rfc_env.env.company.name).replace(' ', '').lower()}
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

                        if rfc_create(rfc_env, result):
                            consumer.acknowledge(msg)

    def rfc_create(rfc_env, rfc_data):
        rfc_reference = rfc_data['Request_For_Catalogue_Ref']
        rfc_description = rfc_data['Request_For_Catalogue_Desc']
        seller_info = rfc_data["Seller"]
        buyer_info = rfc_data['Buyer']

        with rfc_env.env.registry.cursor() as new_cr:
            env = api.Environment(new_cr, SUPERUSER_ID, {})
            partner_id = env['res.partner'].search(['|', ('name', '=', buyer_info['buyer_name']), ('vat', '=', buyer_info['tin_no'])], limit=1)

            if not partner_id:
                new_partner = env['res.partner'].create({
                    'name': buyer_info['buyer_name'],
                    'company_type': 'company',
                    'vat': str(buyer_info['tin_no']),
                    'phone': str(buyer_info['tin_no']),
                    'email': str(buyer_info['tin_no'])}
                )
                partner_id = new_partner

            if not env['sale.order.catalogue_request'].search([('partner_id', '=', partner_id.id), ('partner_rfc_reference', '=', rfc_reference['RFC_Reference'])]):
                rfc_request = env['sale.order.catalogue_request'].create(
                    {
                        'partner_id': partner_id.id,
                        'requested_date': rfc_description['Date'] or None,
                        'expire_date': rfc_description['Expected_Date'] or None,
                        'pass_to_prospective_customer': rfc_reference['pass_to_prospective_customer'] == 'True',
                        'catalogue_with_price': rfc_reference['with_Price'] == 'True',
                        'trade_terms': rfc_description['trade_terms'],
                        'descriptive_literature': rfc_description['Descriptive_Literature'] or None,
                        'condition': rfc_description['Condition'] or None,
                        'partner_rfc_reference': rfc_reference['RFC_Reference'] or None,
                    }
                )

                sales_all_document_users = env.ref('sales_team.group_sale_salesman_all_leads').users
                for user in sales_all_document_users:
                    dead_line = rfc_data['Request_For_Catalogue_Desc']['Expected_Date']
                    activity_type = env.ref('mail.mail_activity_data_todo')

                    env['mail.activity'].create({
                        'display_name': 'Addis Systems Sale Order',
                        'summary': _('New Catalogue Request from %s', rfc_request.partner_id.name),
                        'date_deadline': dead_line,
                        'user_id': user.id,
                        'res_id': rfc_request.id,
                        'res_model_id': env.ref('addis_systems_catalogue_and_order_exchange.model_sale_order_catalogue_request').id,
                        'activity_type_id': activity_type.id
                    })
                return rfc_request

    request_for_catalogue_pulsar_waiter(request_for_catalogue_env)


def catalogue_consumer_asynch(catalogue_env):
    catalogue_quotation_avro = CatalogueQuotations.catalogue_quotation_schema
    catalogue_quotation_schema = avro.schema.parse(json.dumps(catalogue_quotation_avro))

    def catalogue_pulsar_waiter(cat_env):
        so_client = consumer = None
        try:
            so_client = pulsar.Client("pulsar://196.189.124.178:6650")
        except Exception as e:
            raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
        finally:
            if so_client:
                topic_name = "persistent://" + cat_env.env.company.name.replace(' ', '').lower() + "/catalogue/catalogue"
                consumer_configuration = {"subscription_name": str(cat_env.env.company.name).replace(' ', '').lower()}
                try:
                    consumer = so_client.subscribe(topic_name, **consumer_configuration)
                except Exception as e:
                    _logger.warning("Addis Systems topic subscription couldn't be achieved", e)
                finally:
                    if consumer:
                        while True:
                            if msg := consumer.receive():
                                bytes_writer = io.BytesIO(msg.data())
                                decoder = avro.io.BinaryDecoder(bytes_writer)
                                datum_reader = avro.io.DatumReader(catalogue_quotation_schema)
                                result = datum_reader.read(decoder)

                                if order_create(cat_env, result):
                                    consumer.acknowledge(msg)

    def order_create(cat_env, so_data):
        quotation_ref = so_data['Catalogue_Quotation_Ref']
        quotation_products = so_data['Catalogue_Products']
        quotation_seller = so_data['Seller']
        quotation_buyer = so_data['Buyer']

        with cat_env.env.registry.cursor() as new_cr:
            return _order_create_with_new_db_cursor(new_cr, quotation_seller, quotation_ref, quotation_products)

    def _order_create_with_new_db_cursor(new_cr, quotation_seller, quotation_ref, quotation_products):
        catalogue = None
        env = api.Environment(new_cr, SUPERUSER_ID, {})
        request_id = env['purchase.order.rfc'].search([('name', '=', quotation_ref['RFC_Reference'])], limit=1)
        partner_id = env['res.partner'].search(['|', ('name', '=', quotation_seller['company_name']), ('vat', '=', quotation_seller['tin_no'])], limit=1)

        if not partner_id:
            new_partner = env['res.partner'].create({
                'name': quotation_seller['company_name'],
                'company_type': 'company',
                'vat': str(quotation_seller['tin_no']),
                'phone': str(quotation_seller['tin_no']),
                'email': str(quotation_seller['tin_no'])}
            )
            partner_id = new_partner

        if not env['purchase.order.catalogue'].search([('partner_id', '=', partner_id.id), ('partner_reference', '=', quotation_ref['Catalogue_Request_Reference'])]) and request_id:
            catalogue = env['purchase.order.catalogue'].create(
                {
                    'partner_id': partner_id.id,
                    'pass_to_prospective_customer': quotation_ref["Catalogue_Quotation_Reference"] == "True",
                    'catalogue_rfc_id': request_id.id,
                    'partner_reference': quotation_ref['Catalogue_Request_Reference'],
                }
            )

        for product in quotation_products:
            cat_product = env['purchase.catalogue.product'].search(
                [('seller_id', '=', partner_id.id), ('name', '=', product["Product_Name"]), ('default_code', '=', product["Product_Default_Code"] if product["Product_Default_Code"] != 'None' else '')], limit=1)
            if not cat_product:
                new_cat_product = env['purchase.catalogue.product'].create({
                    'name': product["Product_Name"],
                    'catalogue_request_id': request_id.id,
                    'description': '',
                    'type': product["Product_Type"],
                    'uom_id': env['uom.uom'].search([('name', '=', product["Product_UoM"])], limit=1).id,
                    'seller_id': partner_id.id,
                    'barcode': product["Product_Barcode"] if product["Product_Barcode"] != 'None' else '',
                    'product_price': product["Product_Price"] if request_id.catalogue_with_price else "0",
                    'default_code': product["Product_Default_Code"] if product["Product_Default_Code"] != 'None' else '',
                    'weight': product["Product_Weight"],
                    'volume': product["Product_Volume"],
                    'lead_time': product["Product_Lead_Time"]})
                cat_product = new_cat_product

            else:
                cat_product.catalogue_request_id = request_id.id
                cat_product.product_price = product["Product_Price"] if request_id.catalogue_with_price else "0"
                cat_product.weight = product["Product_Weight"]
                cat_product.volume = product["Product_Volume"]

            env['purchase.order.catalogue.line'].create({'parent_catalogue_id': catalogue.id, 'cat_product_id': cat_product.id})

        dead_line = catalogue.catalogue_rfc_id.expire_date
        activity_type = catalogue.env.ref('mail.mail_activity_data_todo')

        env['mail.activity'].create({
            'display_name': 'Addis Systems Catalogue',
            'summary': _('New Catalogue from %s', catalogue.partner_id.name),
            'date_deadline': dead_line,
            'user_id': request_id.write_uid.id,
            'res_id': catalogue.id,
            'res_model_id': env.ref('addis_systems_catalogue_and_order_exchange.model_purchase_order_catalogue').id,
            'activity_type_id': activity_type.id
        })
        return catalogue

    catalogue_pulsar_waiter(catalogue_env)


def sales_order_consumer_asynch(sale_order_env):
    po_quotation_avro = PurchaseOrder.purchase_order_schema
    po_quotation_schema = avro.schema.parse(json.dumps(po_quotation_avro))

    def sales_order_pulsar_waiter(so_env):
        so_client = consumer = None
        try:
            so_client = pulsar.Client("pulsar://196.189.124.178:6650")
        except Exception as e:
            raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
        finally:
            if so_client:
                topic_name = "persistent://" + so_env.env.company.name.replace(' ', '').lower() + "/orders/salesOrder"
                consumer_configuration = {"subscription_name": str(so_env.env.company.name).replace(' ', '').lower()}
                try:
                    consumer = so_client.subscribe(topic_name, **consumer_configuration)
                except Exception as e:
                    _logger.warning("Addis Systems topic subscription couldn't be achieved", e)
                finally:
                    if consumer:
                        while True:
                            if msg := consumer.receive():
                                bytes_writer = io.BytesIO(msg.data())
                                decoder = avro.io.BinaryDecoder(bytes_writer)
                                datum_reader = avro.io.DatumReader(po_quotation_schema)
                                result = datum_reader.read(decoder)

                                if order_create(so_env, result):
                                    consumer.acknowledge(msg)

    def order_create(so_env, so_data):
        purchase_order_ref = so_data['Purchase_Order_ref']
        purchase_order_description = so_data['Purchase_Order_Desc']
        seller_info = so_data["Seller"]
        buyer_info = so_data['Buyer']
        delivery_info = so_data['Delivery_info']
        purchase_total = so_data['Purchase_total']
        vat_breakdown = so_data['Vat_breakdown']

        with so_env.env.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            partner_id = env['res.partner'].search(['|', ('name', '=', buyer_info['buyer_name']), ('vat', '=', buyer_info['tin_no'])])
            if so_exist := env['sale.order'].search([('client_order_ref', '=', purchase_order_ref['RFQ_ref_no']), ('partner_id', '=', partner_id.id)]):
                dead_line = so_data['Purchase_Order_Desc']['Order_deadline']
                activity_type = env.ref('mail.mail_activity_data_todo')
                env['mail.activity'].create({
                    'display_name': 'Addis Systems Sale Order',
                    'summary': _('Your Sales Order Has been Confirmed by %s', so_exist.partner_id.name),
                    'date_deadline': dead_line,
                    'user_id': so_exist.catalogue_quotation_id.create_uid.id,
                    'res_id': so_exist.id,
                    'res_model_id': env.ref('sale.model_sale_order').id,
                    'activity_type_id': activity_type.id
                })

                return so_exist
            else:

                catalogue_quotation = env['sale.order.catalogue_quotations'].search([('name', '=', purchase_order_ref['CAT_Reference'])])

                product_lines = []

                if not partner_id:
                    new_partner = env['res.partner'].create({
                        'name': buyer_info['buyer_name'],
                        'company_type': 'company',
                        'vat': str(buyer_info['tin_no']),
                        'phone': str(buyer_info['tin_no']),
                        'email': str(buyer_info['tin_no'])}
                    )
                    partner_id = new_partner

                sales_order = env['sale.order'].create({
                    'partner_id': partner_id.id,
                    'validity_date': None,
                    'date_order': purchase_order_description['Order_deadline'],
                    'pricelist_id': env['product.pricelist'].search([('name', '=', 'Public Pricelist')], limit=1).id,
                    'payment_term_id': None,
                    'user_id': catalogue_quotation.create_uid.id if catalogue_quotation.id else None,
                    'client_order_ref': purchase_order_ref['PO_ref_no'],
                    'catalogue_quotation_id': catalogue_quotation.id or None
                })

                for products in so_data['Purchase_line']:
                    if product_available := env['product.template'].search([('name', '=', products["item_name"])], limit=1):
                        product_product = env['product.product'].search([('product_tmpl_id', '=', product_available.id)], limit=1)
                        # tax_id = self.env['account.tax'].search([('amount_type', '=', products['Line_allowance_code']), ('type_tax_use', '!=', products['period']), ('amount', '=', products['Line_allowance_reason'])], limit=1)
                        product_line = {
                            'product_id': product_product.id,
                            'order_id': sales_order.id,
                            'product_uom_qty': products["qty"],
                            'product_uom': env['uom.uom'].search([('name', '=', products['unit'])]).id,
                            'price_unit': product_available.list_price
                        }
                        product_lines.append(product_line)
                env['sale.order.line'].create(product_lines)

                dead_line = so_data['Purchase_Order_Desc']['Order_deadline']
                activity_type = env.ref('mail.mail_activity_data_todo')

                env['mail.activity'].create({
                    'display_name': 'Addis Systems Sale Order',
                    'summary': _('New Sale Order to Confirm from %s', sales_order.partner_id.name),
                    'date_deadline': dead_line,
                    'user_id': sales_order.catalogue_quotation_id.create_uid.id,
                    'res_id': sales_order.id,
                    'res_model_id': env.ref('sale.model_sale_order').id,
                    'activity_type_id': activity_type.id
                })
                return sales_order

    sales_order_pulsar_waiter(sale_order_env)


def purchase_order_consumer_asynch(purchase_order_env):
    so_quotation_avro = SalesOrder.sales_order_schema
    so_quotation_schema = avro.schema.parse(json.dumps(so_quotation_avro))

    def purchase_order_pulsar_waiter(po_env):
        po_client = consumer = None
        try:
            po_client = pulsar.Client("pulsar://196.189.124.178:6650")
        except Exception as e:
            raise UserError("Connection to Addis Systems could not be achieved. please try later!") from e
        finally:
            if po_client:
                topic_name = "persistent://" + po_env.env.company.name.replace(' ', '').lower() + "/orders/Quotations"
                consumer_configuration = {"subscription_name": str(po_env.env.company.name).replace(' ', '').lower()}
                try:
                    consumer = po_client.subscribe(topic_name, **consumer_configuration)
                except Exception as e:
                    _logger.warning("Addis Systems topic subscription couldn't be achieved", e)
                finally:
                    if consumer:
                        while True:
                            if msg := consumer.receive():
                                bytes_writer = io.BytesIO(msg.data())
                                decoder = avro.io.BinaryDecoder(bytes_writer)
                                datum_reader = avro.io.DatumReader(so_quotation_schema)
                                result = datum_reader.read(decoder)

                                if po_create(po_env, result):
                                    consumer.acknowledge(msg)

    def po_create(po_env, po_data):
        sales_order_ref = po_data['Sales_Order_ref']
        sales_order_description = po_data['Sales_Order_Desc']
        seller_info = po_data["Seller"]
        buyer_info = po_data['Buyer']
        delivery_info = po_data['Delivery_info']
        vat_breakdown = po_data['Vat_breakdown']
        sales_total = po_data['Sales_total']

        with po_env.env.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            if sales_order_description['SO_exchange'] == 'update':
                po = env['purchase.order'].search([('name', '=', sales_order_description['Customer_Order_Ref']), ('state', '=', 'sent')], limit=1)

                po.partner_ref = sales_order_ref["SO_ref_no"]
                for products in po_data['Order_line']:

                    for po_line in po.order_line:

                        if po_line.product_id.name == products['item_name']:
                            po_line.price_unit = float(products['price'])

                return po

            else:
                # New PO
                print('New Purchase Order')

                return None

    purchase_order_pulsar_waiter(purchase_order_env)
