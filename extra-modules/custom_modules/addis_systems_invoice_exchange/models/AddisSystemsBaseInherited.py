from odoo import models


class AddisBaseInvoiceExchangeInherited(models.Model):
    _inherit = 'res.company'

    def addis_system_connection_init(self):
        super(AddisBaseInvoiceExchangeInherited, self).addis_system_connection_init()
        invoice = self.env['account.move']
        # Vendor Bill Consumer Called
        invoice.addis_system_vendor_bill_consumer()
        # Credit Note Consumer Called
        invoice.addis_system_credit_note_consumer()
