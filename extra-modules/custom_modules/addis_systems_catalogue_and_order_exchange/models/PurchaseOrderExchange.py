from odoo import fields, models, api, _
from odoo.http import request

from .addis_systems import addis_systems_producer_controller as as_producer

from .addis_systems import addis_systems_consumer_controller as consumer

import logging
import requests
from threading import Thread, enumerate

_logger = logging.getLogger(__name__)
TIMEOUT = 300


class AddisSystemsRequestForCatalogue(models.Model):
    _name = 'purchase.order.rfc'
    _description = "Request For Catalogue"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_partner_domain(self):
        return [('id', '!=', self.env.company.partner_id.id)]

    name = fields.Char(string="Request For Catalogue Reference", required=True, default=lambda self: _('New'))
    state = fields.Selection([('draft', 'Draft'), ('partial', 'Partially Sent'), ('sent', 'Sent'), ('canceled', 'Canceled')], required=True, default='draft', tracking=True)

    partner_ids = fields.Many2many('res.partner', string='Partners', required=True, domain=_get_partner_domain)
    pass_to_prospective_customer = fields.Boolean(string='Might Pass to Prospective Customer', default=True, tracking=True)
    catalogue_with_price = fields.Boolean(string='With Price', default=True, tracking=True)
    trade_terms = fields.Selection([('fixed_shop', 'Fixed Shop Retailing'), ('itinerant', 'Itinerant Retailing')], required=True, readonly=False, default='fixed_shop')

    requested_date = fields.Date(string='Requested Date', required=True, default=lambda self: fields.Date.context_today(self), tracking=True)
    expire_date = fields.Date(string='Expire Date', required=False, tracking=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, readonly=True)

    descriptive_literature = fields.Html(string='Descriptive Literature', required=True, translate=False,  help="Detail Description on the product being requested")
    condition = fields.Html(string='Condition', required=False, translate=False, help="Other Conditions and description on the exchange terms or conditions")

    child_catalogue_count = fields.Integer(compute='_compute_child_catalogue_count')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.rfc') or _('New')
            return super(AddisSystemsRequestForCatalogue, self).create(vals)

    def cancel_rfc(self):
        self.state = 'canceled'

    def _compute_child_catalogue_count(self):
        for req in self:
            req.child_catalogue_count = self.env['purchase.order.catalogue'].search_count(
                [('catalogue_rfc_id', '=', req.id)])

    def _compute_purchase_order_count(self):
        for req in self:
            req.purchase_order_count = self.env['purchase.order'].search_count(
                [('rfc_id', '=', req.id)])

    def seller_action_send_rfc_to_seller(self):
        tenants_list_url = "http://196.189.124.178:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=TIMEOUT)

        print(tenants_list_url)

        for partner in self.partner_ids:
            rfc_send = None
            if str(partner.name).replace(' ', '').lower() in tenants_list.json():
                try:
                    rfc_send = as_producer.send_request_for_catalogue_order(self, partner)
                except Exception as e:
                    _logger.warning(" %s:Addis Systems Order Exchange Fail for %s", e, self.name)
                    self.state = 'partial' if self.state in ['sent', 'partial'] else 'draft'
                finally:
                    if rfc_send and self.state == 'draft':
                        self.state = 'sent'
            else:
                self.state = 'partial'
                purchase_group_users = self.env.ref('purchase.group_purchase_manager').users
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
                self.message_post(subject='Message Sending Failed',
                                  body=_("The Partner '%s' Seems unregistered for Electronic Exchange", partner.name),
                                  message_type="comment",
                                  partner_ids=purchase_group_users.ids,
                                  subtype_xmlid="mail.mt_comment", notify_by_email=False)



class AddisSystemsCatalogue(models.Model):
    _name = 'purchase.order.catalogue'
    _description = "Catalogue"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_partner_domain(self):
        return [('id', '!=', self.env.company.partner_id.id)]

    name = fields.Char(string="Catalogue Quotation Reference", required=False, default=lambda self: _('New'))
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], required=True, default='draft')
    catalogue_rfc_id = fields.Many2one('purchase.order.rfc', string='RFC ID', required=True)

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, domain=_get_partner_domain)
    partner_reference = fields.Char(string="Partner Reference", required=True)

    pass_to_prospective_customer = fields.Boolean(string='Might Pass to Prospective Customer', default=False)
    catalogue_with_price = fields.Boolean(related='catalogue_rfc_id.catalogue_with_price')

    catalogue_line = fields.One2many('purchase.order.catalogue.line', 'parent_catalogue_id', 'Parent Wizard', copy=True)
    child_quotation_count = fields.Integer(compute='_compute_child_catalogue_quotation_count')

    count_product_transfer = fields.Integer(string="Transferred Product count", compute='_compute_transferred_product_count')

    def _compute_child_catalogue_quotation_count(self):
        for req in self:
            req.child_quotation_count = self.env['purchase.order'].search_count(
                [('catalogue_id', '=', self.id)])

    def _compute_transferred_product_count(self):
        for req in self:
            count = 0
            for line in self.catalogue_line:
                if line.product_tmpl:
                    count = count + 1

            req.count_product_transfer = count

    def action_create_generate_rfq(self):
        if any(line.product_transferred for line in self.catalogue_line):
            quotation_data = {
                "partner_id": self.partner_id.id,
                "currency_id": self.env.company.currency_id.id,
                "date_order": fields.Datetime.now(),
                "date_planned": fields.Datetime.now(),
                "origin": self.catalogue_rfc_id.name,
                "catalogue_id": self.id,
                "updated_price": bool(self.catalogue_with_price),
            }

            quotation = self.env['purchase.order'].create(quotation_data)

            for line in self.catalogue_line:
                if line.product_transferred:
                    quotation_line_data = {
                        "product_id": self.env['product.product'].search([('product_tmpl_id', '=', line.product_tmpl.id)]).id,
                        "product_qty": 1,
                        "order_id": quotation.id,
                        'price_unit': line.product_tmpl.list_price if self.catalogue_with_price else 0
                    }

                    self.env['purchase.order.line'].create(quotation_line_data)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.catalogue') or _('New')
            return super(AddisSystemsCatalogue, self).create(vals)

    def addis_systems_catalogue_digest(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        catalogue_thread_name = 'addis_systems_catalogue_listener'
        if catalogue_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', catalogue_thread_name, self.env.company.name)
            catalogue_message_waiter_thread = Thread(target=consumer.catalogue_consumer_asynch, args=(self,), daemon=False, name=catalogue_thread_name)
            catalogue_message_waiter_thread.daemon = True
            catalogue_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', catalogue_thread_name, self.env.company.name)

class AddisSystemsCatalogueQuotationsLine(models.Model):
    _name = 'purchase.order.catalogue.line'
    _description = 'Catalogue Line'
    _rec_name = 'cat_product_id'

    def _get_default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id').id

    parent_catalogue_id = fields.Many2one('purchase.order.catalogue', 'Parent Quotation', index=True, ondelete='cascade', required=False)
    catalogue_with_price = fields.Boolean(related='parent_catalogue_id.catalogue_with_price')

    cat_product_id = fields.Many2one('purchase.catalogue.product', 'Product', required=False)

    type = fields.Selection(related='cat_product_id.type')
    cat_product_uom_id = fields.Many2one(related='cat_product_id.uom_id')
    barcode = fields.Char(related='cat_product_id.barcode')
    default_code = fields.Char(related='cat_product_id.default_code')

    product_price = fields.Float(related='cat_product_id.product_price')

    weight = fields.Float(related='cat_product_id.weight')
    volume = fields.Float(related='cat_product_id.volume')
    lead_time = fields.Float(related='cat_product_id.lead_time')

    product_transferred = fields.Boolean(related='cat_product_id.product_transferred')

    product_tmpl = fields.Many2one(related='cat_product_id.product_tmpl')

    product_create = fields.Boolean(string="Create", readonly=False, store=False)

    def action_transfer_to_own_catalogue(self):
        product_data = {
            'name': self.cat_product_id.name,
            'detailed_type': self.cat_product_id.type,
            'default_code': self.cat_product_id.default_code,
            'barcode': self.cat_product_id.barcode,
            'weight': self.cat_product_id.weight,
            'volume': self.cat_product_id.volume,
            'list_price': self.cat_product_id.product_price
        }

        if product := self.env['product.template'].create([product_data]):
            self.cat_product_id.product_transferred = True
            self.cat_product_id.product_tmpl = product.id
class AddisPurchaseExchangeInherited(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def partner_filter(self):
        return {'domain': {'partner_id': [('id', '!=', self.company_id.partner_id.id)]}}

    e_ordered = fields.Boolean(string="Order Sent")
    partner_e_invoicing = fields.Boolean(string='is E-Invoice User', default=False)

    catalogue_id = fields.Many2one('purchase.order.catalogue', 'Catalogue Id', required=False)
    rfc_id = fields.Many2one(related='catalogue_id.catalogue_rfc_id')
    updated_price = fields.Boolean(string="Updated Price", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        tenants_list_url = "http://196.189.124.178:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=TIMEOUT)
        for vals in vals_list:
            partner = self.env['res.partner'].search([('id', '=', vals.get('partner_id'))])
            if str(partner.name).replace(' ', '').lower() in tenants_list.json():
                vals.update({'partner_e_invoicing': True})

        return super(AddisPurchaseExchangeInherited, self).create(vals_list)

    def button_confirm(self):
        # Temporary method for restricting user sending e-invoice to partner
        is_partner_e_invoice_user = False
        tenants_list_url = "http://196.189.124.178:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=TIMEOUT)
        if str(self.partner_id.name).replace(' ', '').lower() in tenants_list.json():
            is_partner_e_invoice_user = True

            if self.catalogue_id:
                try:
                    as_producer.send_purchase_quotation_price_request(self)
                except Exception as e:
                    _logger.warning("%s:Addis Systems Order Exchange Fail for %s", e, self.name)

        self.partner_e_invoicing = is_partner_e_invoice_user

        return super(AddisPurchaseExchangeInherited, self).button_confirm()

    def send_purchase_quotation_price_request(self):
        po_send = None
        try:
            po_send = as_producer.send_purchase_quotation_price_request(self)
        except Exception as e:
            _logger.warning("%s:Addis Systems Order Exchange Fail for %s", e, self.name)
            self.e_ordered = False
        finally:
            if po_send:
                self.e_ordered = True
                self.state = 'sent'

    def send_purchase_order_confirmed_e_order(self):
        po_send = None
        try:
            po_send = as_producer.send_purchase_quotation_price_request(self)
        except Exception as e:
            _logger.warning("%s:Addis Systems Order Exchange Fail for %s", e, self.name)
            self.e_ordered = False
        finally:
            if po_send:
                self.e_ordered = True

    def addis_systems_catalogue_quotation_digest(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        cd_thread_name = 'addis_systems_purchase_order_listener'
        if cd_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', cd_thread_name, self.env.company.name)
            po_message_waiter_thread = Thread(target=consumer.purchase_order_consumer_asynch, args=(self,), name=cd_thread_name)
            po_message_waiter_thread.daemon = True
            po_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', cd_thread_name, self.env.company.name)

class AddisPurchaseOrderLineExchangeInherited(models.Model):
    _inherit = 'purchase.order.line'

    catalogue_id = fields.Many2one(related="order_id.catalogue_id")
