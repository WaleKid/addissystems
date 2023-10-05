from odoo import models


class AddisBaseSalesPurchaseExchangeInherited(models.Model):
    _inherit = 'res.company'

    def addis_system_connection_init(self):
        root = super(AddisBaseSalesPurchaseExchangeInherited, self).addis_system_connection_init()
        if root and root["sales_client"]:
            client = root["sales_client"]
            # Request For Catalogue Consumer Caller
            self.env['sale.order.catalogue_request'].addis_systems_request_for_catalogue_digest(client)
            # Catalogue Consumer Caller
            self.env['purchase.order.catalogue'].addis_systems_catalogue_digest(client)
            # Catalogue Consumer Caller
            self.env['sale.order'].addis_systems_sales_order_digest(client)
            # Catalogue Quotation Consumer Called
            self.env['purchase.order'].addis_systems_catalogue_quotation_digest(client)
        else:
            return


