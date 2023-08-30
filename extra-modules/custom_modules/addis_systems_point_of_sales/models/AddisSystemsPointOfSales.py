from odoo import fields, models


class AddisSystemsPointOfSalesConfigInherited(models.Model):
    _inherit = 'pos.config'

    auto_invoice = fields.Boolean(default='True', help="If This field is checked the all pos orders will have invoice record attached to the order.")
    default_customer = fields.Boolean(default='True', string='Default Customer', help="If This field is checked customer filed will be populated automatically.")
    auto_customer_id = fields.Many2one('res.partner', string='Walk in Customer', help="If This field is checked customer filed will be populated automatically.")

class AddisSystemsPointOfSalesConfigREsConfigInherited(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_auto_invoice = fields.Boolean(related='pos_config_id.auto_invoice',help="If This field is checked the all pos orders will have invoice record attached to the order.", readonly=False)
    pos_default_customer = fields.Boolean( related='pos_config_id.default_customer',help="If This field is checked customer filed will be populated automatically.", readonly=False)
    pos_auto_customer_id = fields.Many2one('res.partner', related='pos_config_id.auto_customer_id', readonly=False)

class AddisSystemsPointOfSales(models.Model):
    _inherit = 'pos.order'

    IRN = fields.Char(related='account_move.IRN')
    acknowledgement_number = fields.Char(related='account_move.acknowledgement_number')

    def ack_and_irn(self):
        return self.IRN