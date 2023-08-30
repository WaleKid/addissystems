from odoo import fields, models, api


class AddisSystemsCatalogueRequestCreateWizard(models.TransientModel):
    _name = 'sale.order.catalogue_request.quot_wizard'
    _description = 'Catalogue Quotations Create Wizard'

    name = fields.Char(string="Name")

    catalogue_request = fields.Many2one('sale.order.catalogue_request', string="Catalogue Request")

    pass_to_prospective_customer = fields.Boolean(related='catalogue_request.pass_to_prospective_customer', string='Might Pass to Prospective Customer')
    catalogue_with_price = fields.Boolean(related='catalogue_request.catalogue_with_price', string='With Price')

    trade_terms = fields.Selection(related='catalogue_request.trade_terms', string='Trade Terms')

    descriptive_literature = fields.Html(related='catalogue_request.descriptive_literature')
    condition = fields.Html(related='catalogue_request.condition')

    catalogue_product_line = fields.One2many('sale.order.catalogue_request.quot_wizard.line', 'parent_wizard_id', 'Parent Wizard', copy=True)

    def _get_default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    def generate_quotation(self):
        product_line = []
        for line in self.catalogue_product_line:
            if self.catalogue_with_price:
                quotation_line = self.env['sale.order.catalogue_quotations.line'].create({'product_id': line.product_id.id, 'product_price': line.product_price})
            else:
                quotation_line = self.env['sale.order.catalogue_quotations.line'].create({'product_id': line.product_id.id})
            product_line += [quotation_line.id]
        create_quotation = self.env['sale.order.catalogue_quotations'].create(
            {'partner_id': self.catalogue_request.partner_id.id, 'pass_to_prospective_customer': self.pass_to_prospective_customer, 'catalogue_request_id': self.catalogue_request.id, 'catalogue_quotation_line': product_line})

        if create_quotation:
            self.catalogue_request.state = 'quoted'

        for activity in self.env['mail.activity'].search([('res_id', '=', self.catalogue_request.id), ('user_id', '!=', self.env.user.id)]):
            activity.unlink()

        return create_quotation

    def generate_quotation_and_send(self):
        product_line = []
        for line in self.catalogue_product_line:
            if self.catalogue_with_price:
                quotation_line = self.env['sale.order.catalogue_quotations.line'].create({'product_id': line.product_id.id, 'product_price': line.product_price})
            else:
                quotation_line = self.env['sale.order.catalogue_quotations.line'].create({'product_id': line.product_id.id})
            product_line += [quotation_line.id]
        create_quotation = self.env['sale.order.catalogue_quotations'].create(
            {'partner_id': self.catalogue_request.partner_id.id, 'pass_to_prospective_customer': self.pass_to_prospective_customer, 'catalogue_request_id': self.catalogue_request.id, 'catalogue_quotation_line': product_line})

        sent = create_quotation.seller_action_send_catalogue_quotation_to_buyer()

        if sent:
            self.catalogue_request.state = 'sent'

        for activity in self.env['mail.activity'].search([('res_id', '=', self.catalogue_request.id), ('user_id', '!=', self.env.user.id)]):
            activity.unlink()



        return create_quotation


class AddisSystemsCatalogueRequestCreateWizardLine(models.TransientModel):
    _name = 'sale.order.catalogue_request.quot_wizard.line'
    _description = 'Catalogue Quotations Create Wizard'

    def _get_default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    parent_wizard_id = fields.Many2one('sale.order.catalogue_request.quot_wizard', 'Parent Wizard', index=True, ondelete='cascade', required=False)

    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id', store=True, index=True)

    product_category = fields.Many2one('product.category', related='product_id.categ_id')

    product_price = fields.Float(related='product_tmpl_id.list_price')

    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', default=_get_default_product_uom_id, required=False, help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control",
                                     domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")

    @api.onchange('product_id')
    def product_filter(self):
        product_ids = [i.product_id.id for i in self.parent_wizard_id.catalogue_product_line if i.product_id]

        return {'domain': {'product_id': [('id', 'not in', product_ids)]}}
