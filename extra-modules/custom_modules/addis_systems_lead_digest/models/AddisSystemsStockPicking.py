from odoo import fields, models, api
import asyncio

from .avro_schema import dispatch_schema as schema
from .addis_systems import producers as producer


class AddisSystemsStockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        dispatch_schema = schema.dispatch_avro
        parent_validate = super(AddisSystemsStockPicking, self).button_validate()
        asyncio.run(producer.dispatch_producer(self, self))

        # return parent_validate