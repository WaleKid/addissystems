from odoo import fields, models, api
from odoo.tools.safe_eval import json
from odoo.exceptions import ValidationError, AccessError

import avro.schema
from datetime import datetime
from avro.io import DatumWriter
import io
import asyncio
from odoo.tools.misc import formatLang

import pulsar
import logging
from num2words import num2words

from .avro_schema import InvoiceAcknowledgement
from .avro_schema import logSchema
from .addis_systems import addis_systems_consumer_controller as consumer
from .addis_systems import addis_systems_producer_controller as producer
from threading import Thread, enumerate

_logger = logging.getLogger(__name__)

TIMEOUT = 150


class AddisAccountTaxInherited(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
        prepare_tax = super(AddisAccountTaxInherited, self)._prepare_tax_totals(base_lines, currency, tax_lines=None)
        non_taxable_amount = 0
        taxable_amount = 0
        tax_amount = 0
        for line in base_lines:
            if not line['taxes']:
                non_taxable_amount += line['price_unit'] * line['quantity']
            else:
                taxable_amount += line['price_unit'] * line['quantity']

        if prepare_tax['groups_by_subtotal']:
            dic_items = dict(prepare_tax['groups_by_subtotal'])
            groups_by_subtotal_dic = dic_items.get('Untaxed Amount')[0]

            tax_amount = groups_by_subtotal_dic['tax_group_amount']
        #
        prepare_tax['non_taxable_amount'] = non_taxable_amount
        prepare_tax['taxable_amount'] = taxable_amount
        prepare_tax['taxable_amount_formatted'] = formatLang(self.env, taxable_amount, currency_obj=currency)
        prepare_tax['non_taxable_amount_formatted'] = formatLang(self.env, non_taxable_amount, currency_obj=currency)
        #
        prepare_tax['tax_amount'] = tax_amount
        prepare_tax['tax_amount_formatted'] = formatLang(self.env, tax_amount, currency_obj=currency)
        #
        prepare_tax['grand_total_amount'] = taxable_amount + non_taxable_amount + tax_amount
        prepare_tax['grand_total_amount_formatted'] = formatLang(self.env,
                                                                 taxable_amount + non_taxable_amount + tax_amount,
                                                                 currency_obj=currency)
        #
        prepare_tax['subtotals_order'] = ['Subtotal', 'Taxable Amount', 'Non Taxable Amount', 'Tax(15%)']

        return prepare_tax


class AddisInvoiceExchangeInherited(models.Model):
    _inherit = 'account.move'

    @api.onchange('partner_id')
    def partner_filter(self):
        return {'domain': {'partner_id': [('id', '!=', self.company_id.partner_id.id)]}}

    IRN = fields.Char(string='IRN')
    acknowledgement_number = fields.Char(string='Acknowledgement Number')
    acknowledgement_date = fields.Char(string='Acknowledgement Date')
    signed_invoice = fields.Char(string='Signed Invoice')
    signed_qr_code = fields.Char(string='Signed QR Code')
    created_date = fields.Char(string='Created Date')
    created_by = fields.Char(string='Created By')
    invoice_status = fields.Selection([('pending', 'Pending'), ('registered', 'Registered'), ('failed', 'Failed')],
                                      required=True, readonly=True, copy=False, tracking=True, default='pending')

    e_invoicing = fields.Boolean(string='E-invoicing Sent', default=False)
    partner_e_invoicing = fields.Boolean(string='is E-Invoice User', default=False)

    #   --------------- Override Methods   ---------------

    def amount_in_words(self, data):
        return str(num2words(data)).title()

    @api.model_create_multi
    def create(self, vals_list):
        create_parent = super(AddisInvoiceExchangeInherited, self).create(vals_list)
        for lines in create_parent.invoice_line_ids:
            if lines.price_unit <= 0 or lines.quantity <= 0:
                raise ValidationError("1 Price or Quantity can not be 0 or Negative")
        return create_parent

    def write(self, vals):
        return super(AddisInvoiceExchangeInherited, self).write(vals)

    #   --------------- Report Methods    ---------------

    def signed_invoice_decode_for_print(self, signed_qr_code):
        payment_json = {"invoice_reference": self.name, "customer": self.partner_id.name,
                        "customer_tin": self.partner_id.vat}
        return str(payment_json)

    #   --------------- Exchange Methods    ---------------

    def seller_invoice_to_buyer(self):
        invoice_ack_avro = InvoiceAcknowledgement.invoice_acknowledgement_schema
        client = pulsar.Client("pulsar://196.189.124.178:6650")
        exchange_producer = client.create_producer(
            'persistent://addisadmin/invoice/exchange')

        message = {
            'IRN': self.IRN or '',
            'AckNo': self.acknowledgement_number if self.IRN else '',
            'AckDt': self.acknowledgement_date or '',
            'Signed_invoice': self.signed_invoice or '',
            'Created_Date': self.created_date or '',
            'Created_by': self.created_by or '',
            'Inv_Status': self.invoice_status.lower() if self.invoice_status else '',
            'Signed_QRCode': self.signed_qr_code or ''}

        schema = avro.schema.parse(json.dumps(invoice_ack_avro))
        writer = DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(message, encoder)

        avro_bytes = bytes_writer.getvalue()
        exchange_producer.send(avro_bytes, properties={"key": str(self.partner_id.name).replace(' ', '').lower()})
        self.e_invoicing = True

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
        #             "InvoiceCreatedDate": str(datetime.now()),
        #             "InvoiceID": str(self.name or None),
        #             "CompanyName": str(self.env.company.name).replace(' ', '').lower(),
        #             "ErrorResponse": "",
        #             "ErrorStatus": {
        #                 "sentStatus": {
        #                     "Sent_INV": "",
        #                     "Sent_INV_AT": ""
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
        #                     "Ack_Exchange_INV": "True",
        #                     "Ack_Exchange_INV_AT": str(fields.Datetime.now())
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

        client.close()

    def action_post(self):
        parent_post = super(AddisInvoiceExchangeInherited, self).action_post()
        if self.move_type == 'out_invoice':
            if asyncio.run(producer.invoice_producer(self)):
                # asyncio.run(producer.invoice_log_tracking_producer_consume(self))
                return parent_post
            else:
                raise AccessError("Couldn't register the Invoice please try again later. Sorry for the inconvenience")


    def addis_system_vendor_bill_consumer(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        vb_thread_name = 'addis_systems_vendor_bill_listener'
        if vb_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', vb_thread_name, self.env.company.name)
            vb_message_waiter_thread = Thread(target=consumer.vendor_bill_consumer_asynch, args=(self,),name=vb_thread_name)
            vb_message_waiter_thread.daemon = True
            vb_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', vb_thread_name, self.env.company.name)
