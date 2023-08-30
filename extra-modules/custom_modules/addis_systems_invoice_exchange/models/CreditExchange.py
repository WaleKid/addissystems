from odoo import models
from odoo.tools.safe_eval import json
from odoo.exceptions import ValidationError, AccessError

import avro.schema
from avro.io import DatumWriter
import io
from threading import Thread, enumerate

import pulsar
import asyncio
import logging

from .avro_schema import InvoiceAcknowledgement
from .addis_systems import addis_systems_producer_controller as producer
from .addis_systems import addis_systems_consumer_controller as consumer

_logger = logging.getLogger(__name__)
TIMEOUT = 300


class AddisRefundExchangeInherited(models.Model):
    _inherit = 'account.move'

    def seller_refund_to_buyer(self):
        invoice_ack_schema = InvoiceAcknowledgement.invoice_acknowledgement_schema
        client = pulsar.Client("pulsar://196.189.124.178:6650")
        exc_producer = client.create_producer('persistent://addisadmin/refund/exchange')
        message = {
            'IRN': self.IRN or '',
            'AckNo': self.acknowledgement_number or '',
            'AckDt': self.acknowledgement_date or '',
            'Signed_invoice': self.signed_invoice or '',
            'Created_Date': self.created_date or '',
            'Created_by': self.created_by or '',
            'Inv_Status': self.invoice_status.lower() if self.invoice_status else '',
            'Signed_QRCode': self.signed_qr_code or ''}

        schema = avro.schema.parse(json.dumps(invoice_ack_schema))
        writer = DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(message, encoder)

        avro_bytes = bytes_writer.getvalue()
        exc_producer.send(avro_bytes, properties={"key": str(self.partner_id.name).replace(' ', '').lower()})
        self.e_invoicing = True

    def action_post(self):
        parent_post = super(AddisRefundExchangeInherited, self).action_post()
        if self.move_type == 'in_refund':  # Journal Entry
            if  asyncio.run(producer.refund_producer(self)):
                # asyncio.run(producer.refund_log_tracking_producer_consume(self))
                return parent_post
            else:
                raise AccessError("Couldn't register the Refund please try again later. Sorry for the inconvenience")

    def _post(self, soft=True):
        parent_post = super(AddisRefundExchangeInherited, self)._post()
        if not self.env['pos.order'].search([('account_move', '=', self.id)]):
            return  parent_post
        if asyncio.run(producer.invoice_producer(self)):
            # asyncio.run(producer.invoice_log_tracking_producer_consume(self))
            return parent_post
        else:
            raise AccessError("Couldn't register the Order please try again later.\nSorry for the inconvenience")

    def addis_system_credit_note_consumer(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        cn_thread_name = 'addis_systems_credit_note_listener'
        if cn_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', cn_thread_name, self.env.company.name)
            cn_message_waiter_thread = Thread(target=consumer.credit_note_consumer_asynch, args=(self,),
                                              name=cn_thread_name)
            cn_message_waiter_thread.daemon = True
            cn_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', cn_thread_name, self.env.company.name)
