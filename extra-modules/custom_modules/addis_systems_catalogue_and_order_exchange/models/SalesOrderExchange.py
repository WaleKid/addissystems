from odoo import fields, models, api, _
from odoo.http import request

from .addis_systems import addis_systems_producer_controller as as_producer

from .addis_systems import addis_systems_consumer_controller as consumer

import logging
import requests
from threading import Thread, enumerate

_logger = logging.getLogger(__name__)
TIMEOUT = 300


class AddisSystemsCatalogueRequest(models.Model):
    _name = 'sale.order.catalogue_request'
    _description = "Catalogue Requests"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)

    name = fields.Char(string="Catalogue Request Reference", required=True, default=lambda self: _('New'))
    state = fields.Selection([('new', 'New'), ('quoted', 'Quoted'), ('sent', 'Sent')], required=True, default='new')

    pass_to_prospective_customer = fields.Boolean(string='Might Pass to Prospective Customer')
    catalogue_with_price = fields.Boolean(string='With Price')
    trade_terms = fields.Selection([('itinerant', 'Itinerant Retailing'), ('fixed_shop', 'Fixed Shop Retailing')], required=False, readonly=False, copy=False, tracking=True)

    requested_date = fields.Date(string='Requested Date', required=True, default=lambda self: fields.Date.context_today(self))
    expire_date = fields.Date(string='Expire Date', required=False)

    descriptive_literature = fields.Html(string='Descriptive Literature', required=True)
    condition = fields.Html(string='Condition')

    #   Catalogue references

    partner_rfc_reference = fields.Char(string="Partner RFC Reference", required=True)
    child_catalogue_quotation_count = fields.Integer(compute='_compute_child_catalogue_quotation_count')

    def _compute_child_catalogue_quotation_count(self):
        for req in self:
            req.child_catalogue_quotation_count = self.env['sale.order.catalogue_quotations'].search_count(
                [('catalogue_request_id', '=', self.id)])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.catalogue.request') or _('New')
            return super(AddisSystemsCatalogueRequest, self).create(vals)

    def action_create_catalogue_quotation(self):
        new_wizard = self.env['sale.order.catalogue_request.quot_wizard'].create({'name': "New Catalog Quotation", 'catalogue_request': self.id})
        view_id = self.env.ref('addis_systems_catalogue_and_order_exchange.addis_systems_catalogue_quotation_create_wizard_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Confirm'),
            'view_mode': 'form',
            'res_model': 'sale.order.catalogue_request.quot_wizard',
            'target': 'new',
            'res_id': new_wizard.id,
            'views': [[view_id, 'form']],
        }

    def addis_systems_request_for_catalogue_digest(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        rfc_thread_name = 'addis_systems_request_for_catalogue_listener'
        if rfc_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', rfc_thread_name, self.env.company.name)
            rfc_message_waiter_thread = Thread(target=consumer.request_for_catalogue_consumer_asynch, args=(self,), name=rfc_thread_name)
            rfc_message_waiter_thread.daemon = True
            rfc_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', rfc_thread_name, self.env.company.name)


class AddisSystemsCatalogueQuotations(models.Model):
    _name = 'sale.order.catalogue_quotations'
    _description = "Catalogue Quotations"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Catalogue Quotation Reference", required=False, default=lambda self: _('New'))
    catalogue_request_id = fields.Many2one('sale.order.catalogue_request', string='Catalogue Request ID', readonly=True)

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], required=True, default='draft')
    pass_to_prospective_customer = fields.Boolean(string='Might Pass to Prospective Customer', default=False)
    with_price = fields.Boolean(related='catalogue_request_id.catalogue_with_price')

    descriptive_literature = fields.Html(related='catalogue_request_id.descriptive_literature', string='Descriptive Literature')
    condition = fields.Html(related='catalogue_request_id.condition', string='Condition')

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, readonly=True)

    partner_rfc_reference = fields.Char(related='catalogue_request_id.partner_rfc_reference', string='Partner Reference', required=False)
    catalogue_quotation_line = fields.One2many('sale.order.catalogue_quotations.line', 'parent_quotation_id', 'Parent Wizard', copy=True)

    def seller_action_send_catalogue_quotation_to_buyer(self):
        tenants_list_url = "http://196.189.124.178:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=TIMEOUT)

        catalogue_quotation_send = None

        if str(self.partner_id.name).replace(' ', '').lower() in tenants_list.json():
            try:
                catalogue_quotation_send = as_producer.send_catalogue_quotation(self)
            except Exception as e:
                _logger.warning("%s:Addis Systems Order Exchange Fail for %s", e, self.name)
                self.state = 'draft'
            finally:
                if catalogue_quotation_send:
                    self.state = 'sent'
                    self.catalogue_request_id.state = 'sent'
        else:
            sales_all_doc_group_users = self.env.ref('sales_team.group_sale_salesman_all_leads').users

            base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            self.message_post(subject='Addis Systems: Message Sending Failed', type='notification',
                              body=_("The Partner '%s' Seems unregistered for Electronic Exchange", self.partner_id.name),
                              message_type="notification",
                              partner_ids=sales_all_doc_group_users.ids,
                              subtype_xmlid="mail.mt_comment", notify_by_email=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.catalogue.quotation') or _('New')
            return super(AddisSystemsCatalogueQuotations, self).create(vals)


class AddisSystemsCatalogueQuotationsLine(models.Model):
    _name = 'sale.order.catalogue_quotations.line'
    _description = 'Catalogue Quotations Line'
    _rec_name = 'parent_quotation_id'

    def _get_default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")

    parent_quotation_id = fields.Many2one('sale.order.catalogue_quotations', 'Parent Quotation', index=True, ondelete='cascade', required=False)
    product_id = fields.Many2one('product.product', 'Product', required=False)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id', store=True, index=True)

    with_price = fields.Boolean(related='parent_quotation_id.with_price')
    product_price = fields.Float(string="Sales Price", default=0)

    product_uom_id = fields.Many2one('uom.uom', 'Product Unit of Measure', default=_get_default_product_uom_id, required=False, help="Unit of Measure (Unit of Measure) is the unit of measurement for the inventory control", domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')

    product_type = fields.Selection(related='product_tmpl_id.detailed_type')
    default_code = fields.Char(related='product_id.default_code')

    weight = fields.Float(related='product_id.weight')
    volume = fields.Float(related='product_id.volume')
    lead_time = fields.Float(related='product_tmpl_id.sale_delay')

    @api.onchange('product_id')
    def product_filter(self):
        product_ids = [i.product_id.id for i in self.parent_quotation_id.catalogue_quotation_line if i.product_id]

        return {'domain': {'product_id': [('id', 'not in', product_ids)]}}


class AddisSalesExchangeInherited(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def partner_filter(self):
        return {'domain': {'partner_id': [('id', '!=', self.company_id.partner_id.id)]}}

    catalogue_quotation_id = fields.Many2one('sale.order.catalogue_quotations', 'Catalogue quotation', required=False)
    with_price = fields.Boolean(related='catalogue_quotation_id.with_price')


    def send_sales_order_quotation_update_e_order(self):
        so_send = None
        try:
            so_send = as_producer.send_rfq_update_for_buyer(self)
        except Exception as e:
            _logger.warning("%s:Addis Systems Order Exchange Fail for %s", e, self.name)
        finally:
            if so_send:
                self.state = 'sent'

    def action_confirm(self):
        try:
            as_producer.send_sales_order_for_vendor(self)
        except Exception as e:
            _logger.warning("%s:Addis Systems Order Exchange Fail for %s", e, self.name)
        return super(AddisSalesExchangeInherited, self).action_confirm()

    def addis_systems_sales_order_digest(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        so_thread_name = 'addis_systems_sales_order_listener'
        if so_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', so_thread_name, self.env.company.name)
            so_message_waiter_thread = Thread(target=consumer.sales_order_consumer_asynch, args=(self,), name=so_thread_name)
            so_message_waiter_thread.daemon = True
            so_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', so_thread_name, self.env.company.name)


class AddisSalesLineExchangeInherited(models.Model):
    _inherit = 'sale.order.line'

    catalogue_quotation_id = fields.Many2one(related='order_id.catalogue_quotation_id')
    client_order_ref = fields.Char(related='order_id.client_order_ref')
