from odoo import fields, models, tools


# Products
# Product Variants


class AddisSystemsCatalogueProducts(models.Model):
    _name = 'purchase.catalogue.product'
    _description = 'Catalogue Products'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @tools.ormcache()
    def _get_default_uom_id(self):
        return self.env.ref('uom.product_uom_unit')

    name = fields.Char('Name', index=True, required=True, translate=True)
    catalogue_request_id = fields.Many2one('purchase.order.rfc', string='RFC ID', required=True)
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the product without removing it.")
    sequence = fields.Integer('Sequence', default=1, help='Gives the sequence order when displaying a product list')
    description = fields.Html('Description', translate=True)
    type = fields.Selection(selection=[('product', 'Storable'), ('service', 'Service'), ('consu', 'Consumable'), ('event', 'Event Ticket')], compute='_compute_type', store=True, readonly=False)

    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', default=_get_default_uom_id, required=True, help="Default unit of measure used for all stock operations.") # Done

    seller_id = fields.Many2one('res.partner', string='Vendors',  help="The vendor that send the catalogue product")

    barcode = fields.Char('Barcode') # Done
    product_price = fields.Float('Product Price', store=True, default=0)
    default_code = fields.Char('Partner Reference', store=True) # Done

    weight = fields.Float(string='Weight', default=0, required=True, help="Weight of the Product in KG")
    volume = fields.Float(string='Volume', default=0, required=True, help="Volume of the Product in m3")
    lead_time = fields.Float(string='Lead Time', default=0, required=True, help="Partner Lead Time of the product in days")

    product_transferred = fields.Boolean(string="Transferred", default=False, readonly=False)
    product_tmpl = fields.Many2one('product.template', string='Product Reference', required=False, readonly=True)


class AddisSystemsCatalogueProductsVariants(models.Model):
    _name = 'purchase.catalogue.product.variant'
    _description = 'Catalogue Products Variants'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @tools.ormcache()
    def _get_default_uom_id(self):
        return self.env.ref('uom.product_uom_unit')

    parent_product_id = fields.Many2one('purchase.catalogue.product', 'Parent Catalogue Product', required=True, help="Catalogue Product Variants relation")

    name = fields.Char('Name', index=True, required=True, translate=True)
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the product without removing it.")
    sequence = fields.Integer('Sequence', default=1, help='Gives the sequence order when displaying a product list')
    description = fields.Html('Description', translate=True)
    type = fields.Selection(selection=[('product', 'Storable'), ('service', 'Service'), ('consu', 'Consumable'), ('event', 'Event Ticket')], compute='_compute_type', store=True, readonly=False)

    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', default=_get_default_uom_id, required=True, help="Default unit of measure used for all stock operations.")

    seller_id = fields.Many2one('res.partner', string='Vendors',  help="The vendor that send the catalogue product")

    barcode = fields.Char('Barcode')
    default_code = fields.Char('Internal Reference', store=True)
