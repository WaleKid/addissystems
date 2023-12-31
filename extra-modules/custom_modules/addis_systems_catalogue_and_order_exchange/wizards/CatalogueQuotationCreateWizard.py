from odoo import fields, models, api


class AddisSystemsCatalogueRequestCreateWizard(models.TransientModel):
    _name = 'sale.order.catalogue_request.quot_wizard'
    _description = 'Catalogue Quotations Create Wizard'

    name = fields.Char(string="Name")

    catalogue_request = fields.Many2one('sale.order.catalogue_request', string="Catalogue Request")

    pass_to_prospective_customer = fields.Boolean(related='catalogue_request.pass_to_prospective_customer', string='Pass to Customer')
    catalogue_with_price = fields.Boolean(related='catalogue_request.catalogue_with_price', string='With Price')

    start_date = fields.Date(string='Blanket Date End', required=False, help="Since it's a blanket order the catalogue will have the current product public price, in this field provide the date span the price sent now will be acceptable")
    date_end = fields.Date(string='Blanket Date Start', required=False, help="Since it's a blanket order the catalogue will have the current product public price, in this field provide the date span the price sent now will be acceptable")

    trade_terms = fields.Selection(related='catalogue_request.trade_terms', string='Trade Terms')
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    descriptive_literature = fields.Html(related='catalogue_request.descriptive_literature')
    condition = fields.Html(related='catalogue_request.condition')

    catalogue_product_line = fields.One2many('sale.order.catalogue_request.quot_wizard.line', 'parent_wizard_id', 'Parent Wizard', copy=True)
    line_count = fields.Integer(string='Number of Line', compute='_get_lines_count')

    @api.onchange('catalogue_product_line', 'start_date', 'date_end')
    def _get_lines_count(self):
        for wizard in self:
            if wizard.trade_terms == 'blanket' and wizard.start_date and wizard.date_end or wizard.trade_terms != 'blanket':
                wizard.line_count = len(wizard.catalogue_product_line)
            else:
                wizard.line_count = 0

    def generate_quotation(self):
        product_line = []
        for line in self.catalogue_product_line:
            if self.catalogue_with_price:
                quotation_line = self.env['sale.order.catalogue_quotations.line'].create({'product_id': line.product_id.id, 'product_price': line.product_price})
            else:
                quotation_line = self.env['sale.order.catalogue_quotations.line'].create({'product_id': line.product_id.id})
            product_line += [quotation_line.id]
        create_quotation = self.env['sale.order.catalogue_quotations'].create(
            {'partner_id': self.catalogue_request.partner_id.id, 'pass_to_prospective_customer': self.pass_to_prospective_customer, 'catalogue_request_id': self.catalogue_request.id, 'catalogue_quotation_line': product_line, 'start_date': self.start_date, 'date_end': self.date_end, 'incoterm_id': self.incoterm_id.id})

        if create_quotation:
            self.catalogue_request.state = 'quoted'

        for activity in self.env['mail.activity'].search([('res_id', '=', self.catalogue_request.id), ('user_id', '!=', self.env.user.id)]):
            activity.unlink()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.catalogue_quotations',
            'res_id': create_quotation.id,
            'name': create_quotation.name,
            'view_mode': 'form',
            'views': [(False, "form")],
        }

    def generate_quotation_and_send(self):
        product_line = []
        for line in self.catalogue_product_line:
            if self.catalogue_with_price:
                quotation_line = self.env['sale.order.catalogue_quotations.line'].create({'product_id': line.product_id.id, 'product_price': line.product_price})
            else:
                quotation_line = self.env['sale.order.catalogue_quotations.line'].create({'product_id': line.product_id.id})
            product_line += [quotation_line.id]
        create_quotation = self.env['sale.order.catalogue_quotations'].create(
            {'partner_id': self.catalogue_request.partner_id.id, 'pass_to_prospective_customer': self.pass_to_prospective_customer, 'catalogue_request_id': self.catalogue_request.id, 'catalogue_quotation_line': product_line, 'start_date': self.start_date, 'date_end': self.date_end, 'incoterm_id': self.incoterm_id.id})

        sent = create_quotation.seller_action_send_catalogue_quotation_to_buyer()

        if sent:
            self.catalogue_request.state = 'sent'

        for activity in self.env['mail.activity'].search([('res_id', '=', self.catalogue_request.id), ('user_id', '!=', self.env.user.id)]):
            activity.unlink()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.catalogue_quotations',
            'res_id': create_quotation.id,
            'name': create_quotation.name,
            'view_mode': 'form',
            'views': [(False, "form")],
        }


class AddisSystemsCatalogueRequestCreateWizardLine(models.TransientModel):
    _name = 'sale.order.catalogue_request.quot_wizard.line'
    _description = 'Catalogue Quotations Create Wizard'

    def _get_default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    parent_wizard_id = fields.Many2one('sale.order.catalogue_request.quot_wizard', 'Parent Wizard', index=True, ondelete='cascade', required=False)
    trade_terms = fields.Selection(related='parent_wizard_id.trade_terms', string='Trade Terms')

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
