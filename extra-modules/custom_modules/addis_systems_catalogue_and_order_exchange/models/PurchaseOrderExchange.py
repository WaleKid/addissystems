import datetime
from odoo.exceptions import UserError
from odoo import fields, models, api, _
from odoo.http import request

from .addis_systems import addis_systems_producer_controller as as_producer

from .addis_systems import addis_systems_consumer_controller as consumer

import logging
import requests
from threading import Thread, enumerate

_logger = logging.getLogger(__name__)
TIMEOUT = 300


class AddisSystemsPurchaseRequisitionInherited(models.Model):
    _inherit = 'purchase.requisition'

    catalogue_rfc_id = fields.Many2one('purchase.order.rfc', string='RFC Reference', required=False)
    catalogue_id = fields.Many2one('purchase.order.catalogue', string='Catalogue Reference', required=False)


class AddisSystemsRequestForCatalogue(models.Model):
    _name = 'purchase.order.rfc'
    _description = "Request For Catalogue"
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_partner_domain(self):
        return [('id', '!=', self.env.company.partner_id.id)]

    name = fields.Char(string="RFC Reference", required=True, default=lambda self: _('New'))
    state = fields.Selection([('draft', 'Draft'), ('partial', 'Partially Sent'), ('sent', 'Sent'), ('canceled', 'Canceled')], required=True, default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, readonly=True)

    partner_ids = fields.Many2many('res.partner', string='Partners', required=True, domain=_get_partner_domain)
    pass_to_prospective_customer = fields.Boolean(string='Pass to Customer', tracking=True, help="If this field is set to true the the catalogue received can be passed to third party partner by the customer! NOTICE some company's inventory catalogues might be private")
    catalogue_with_price = fields.Boolean(string='With Price', tracking=True, help="If this field is set to true the the catalogue sent will contain price otherwise the catalogue contain only the products list")
    trade_terms = fields.Selection([('blanket', 'Blanket Order'), ('retail', 'Retailing')], required=True, readonly=False, default='blanket')

    requested_date = fields.Date(string='Requested Date', required=True, default=lambda self: fields.Date.context_today(self), tracking=True, readonly=True)
    expire_date = fields.Date(string='Expire Date', required=False, tracking=True, help="The expire date for the catalogue request, NOTICE: catalogues sent after the expire date won't be accepted by the system and deleted permanently!")

    descriptive_literature = fields.Html(string='Descriptive Literature', required=True, translate=False, help="Detail Description on the product being requested")
    condition = fields.Html(string='Condition', required=False, translate=False, help="Other Conditions and description on the exchange terms or conditions")

    child_catalogue_count = fields.Integer(compute='_compute_child_catalogue_count')
    purchase_order_count = fields.Integer(compute='_compute_rfq_and_purchase_order_count')
    received_products_count = fields.Integer(compute='_compute_received_products_count')
    blanket_order_count = fields.Integer(compute='_compute_blanket_order_count')

    received_products = fields.One2many('purchase.catalogue.product', 'catalogue_request_id', string='Products', compute='_compute_received_products')
    blanket_orders = fields.One2many('purchase.requisition', 'catalogue_rfc_id', string='BO Reference', compute='_compute_blanket_order')

    _sql_constraints = [
        ('catalogue_request', 'unique (name)', 'Catalogue Request can not be identical!')]

    # Count Methods

    def _compute_child_catalogue_count(self):
        for req in self:
            req.child_catalogue_count = self.env['purchase.order.catalogue'].search_count([('catalogue_rfc_id', '=', req.id)])

    def _compute_blanket_order_count(self):
        for req in self:
            for blanket in self.env['purchase.requisition'].search([('catalogue_rfc_id', '=', req.id)]):
                for po in self.env['purchase.order'].search([('requisition_id', '=', blanket.id)]):
                    po.rfc_id = self.id
                    po.catalogue_id = blanket.catalogue_id.id
                    po.incoterm_id = blanket.catalogue_id.incoterm_id.id
            req.blanket_order_count = self.env['purchase.requisition'].search_count([('catalogue_rfc_id', '=', req.id)])

    def _compute_blanket_order(self):
        for req in self:
            for blanket in self.env['purchase.requisition'].search([('catalogue_rfc_id', '=', req.id)]):
                for po in self.env['purchase.order'].search_count([('requisition_id', '=', blanket.id)]):
                    po.rfc_id = self.id
                    po.catalogue_id = blanket.catalogue_id.id
                    po.incoterm_id = blanket.catalogue_id.incoterm_id.id
            req.blanket_orders = self.env['purchase.requisition'].search([('catalogue_rfc_id', '=', req.id)])

    def _compute_rfq_and_purchase_order_count(self):
        for req in self:
            req.purchase_order_count = self.env['purchase.order'].search_count([('rfc_id', '=', req.id)])

    def _compute_received_products_count(self):
        for req in self:
            req.received_products_count = self.env['purchase.catalogue.product'].search_count([('catalogue_request_id', '=', req.id)])

    def _compute_received_products(self):
        for req in self:
            req.received_products = self.env['purchase.catalogue.product'].search([('catalogue_request_id', '=', req.id)])

    @api.onchange('trade_terms')
    def trade_terms_onchange(self):
        self.pass_to_prospective_customer = self.trade_terms != 'blanket'
        self.catalogue_with_price = self.trade_terms == 'blanket'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('descriptive_literature') or not vals.get('expire_date') or not vals.get('partner_ids'):
                raise UserError("Descriptive for the request Should be provided!, please describe the Request in detail in Descriptive Literature field and proceed")
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.rfc') or _('New')

            if vals.get('trade_terms') == 'blanket':
                vals['pass_to_prospective_customer'] = False
                vals['catalogue_with_price'] = True
            else:
                vals['pass_to_prospective_customer'] = True
                vals['catalogue_with_price'] = False

            expire_date = datetime.datetime.strptime(vals.get('expire_date'), '%Y-%m-%d')
            if expire_date.date() < fields.Date.context_today(self):
                raise UserError("Expire Date Cannot be less than Requested Date!")
            return super(AddisSystemsRequestForCatalogue, self).create(vals)

    def cancel_rfc(self):
        self.state = 'canceled'

    def seller_action_send_rfc_to_seller(self):
        tenants_list_url = "http://192.168.100.209:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=TIMEOUT)

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
    catalogue_rfc_id = fields.Many2one('purchase.order.rfc', string='RFC Reference', required=True)
    trade_terms = fields.Selection(related='catalogue_rfc_id.trade_terms', string='Trade Terms')
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    partner_id = fields.Many2one('res.partner', string='Partner', required=True, domain=_get_partner_domain)
    partner_reference = fields.Char(string="Partner Reference", required=True)

    pass_to_prospective_customer = fields.Boolean(string='Pass to Customer', default=False)
    catalogue_with_price = fields.Boolean(related='catalogue_rfc_id.catalogue_with_price')

    catalogue_line = fields.One2many('purchase.order.catalogue.line', 'parent_catalogue_id', 'Parent Wizard', copy=True)

    child_quotation_count = fields.Integer(compute='_compute_child_catalogue_quotation_count')
    child_blanket_count = fields.Integer(compute='_compute_child_blanket_order_count')
    count_product_transfer = fields.Integer(string="Transferred Product count", compute='_compute_transferred_product_count')

    # For Blanket Order Only

    start_date = fields.Date(string='Blanket Date End', required=False)
    date_end = fields.Date(string='Blanket Date Start', required=False)

    def _compute_child_catalogue_quotation_count(self):
        for req in self:
            req.child_quotation_count = self.env['purchase.order'].search_count(
                [('catalogue_id', '=', self.id)])

    def _compute_child_blanket_order_count(self):
        for req in self:
            req.child_blanket_count = self.env['purchase.requisition'].search_count(
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
                "incoterm_id": self.incoterm_id.id
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

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'res_id': quotation.id,
                'name': quotation.name,
                'view_mode': 'form',
                'views': [(False, "form")],
            }

    def action_create_generate_blanket_order(self):
        if any(line.product_transferred for line in self.catalogue_line):
            date_end = fields.Datetime.to_string(datetime.datetime(self.date_end.year, self.date_end.month, self.date_end.day, 20, 59, 59))
            bo_data = {
                "user_id": self.env.user.id,
                "type_id": self.env.ref('purchase_requisition.type_single').id,
                "vendor_id": self.partner_id.id,
                "currency_id": self.catalogue_rfc_id.company_id.currency_id.id,
                "date_end": fields.Datetime.from_string(date_end),
                "ordering_date": self.catalogue_rfc_id.requested_date,
                "schedule_date": None,
                "origin": self.catalogue_rfc_id.name,
                "catalogue_rfc_id": self.catalogue_rfc_id.id,
                "catalogue_id": self.id
            }
            requisition = self.env['purchase.requisition'].create(bo_data)

            for line in self.catalogue_line:
                if line.product_transferred:
                    bo_line_data = {
                        "requisition_id": requisition.id,
                        "product_id": self.env['product.product'].search([('product_tmpl_id', '=', line.product_tmpl.id)]).id,
                        "price_unit": line.product_price,
                        "product_qty": 1,
                        "product_uom_id": line.product_tmpl.uom_po_id.id
                    }

                    self.env['purchase.requisition.line'].create(bo_line_data)

            requisition.action_in_progress()

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.requisition',
                'res_id': requisition.id,
                'name': requisition.name,
                'view_mode': 'form',
                'views': [(False, "form")],
            }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.catalogue') or _('New')
            return super(AddisSystemsCatalogue, self).create(vals)

    def addis_systems_catalogue_digest(self, client):
        if client:
            all_active_thread_names = [thread.name for thread in enumerate()]

            catalogue_thread_name = 'addis_systems_catalogue_listener'
            if catalogue_thread_name not in all_active_thread_names:
                _logger.info('Starting Thread %s for company: %s', catalogue_thread_name, self.env.company.name)
                catalogue_message_waiter_thread = Thread(target=consumer.catalogue_consumer_asynch, args=(self, client), daemon=False, name=catalogue_thread_name)
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

    po_type = fields.Selection(selection=[('manual', 'Manual'), ('retail', 'Retail'), ('blanket', 'Blanket')], string="Purchase Order Type", compute='_compute_po_type', default='manual', required=True)

    e_ordered = fields.Boolean(string="Order Sent")
    partner_e_invoicing = fields.Boolean(string='is E-Invoice User', default=False)

    updated_price = fields.Boolean(string="Updated Price", compute='_compute_price_status', store=True)

    catalogue_id = fields.Many2one('purchase.order.catalogue', 'Catalogue Id', required=False)
    rfc_id = fields.Many2one(related='catalogue_id.catalogue_rfc_id')

    def _compute_po_type(self):
        for po in self:
            if po.requisition_id:
                po.po_type = 'blanket'
            elif po.catalogue_id and po.rfc_id:
                po.po_type = 'retail'
            else:
                po.po_type = 'manual'

    def _compute_price_status(self):
        for po in self:
            po.updated_price = bool(po.requisition_id)
            print()
            if po.requisition_id and po.catalogue_id:
                po.incoterm_id = po.catalogue_id.incoterm_id.id

    @api.model_create_multi
    def create(self, vals_list):
        tenants_list_url = "http://192.168.100.209:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=TIMEOUT)
        for vals in vals_list:
            partner = self.env['res.partner'].search([('id', '=', vals.get('partner_id'))])
            if str(partner.name).replace(' ', '').lower() in tenants_list.json():
                vals.update({'partner_e_invoicing': True})

            if not vals.get('catalogue_id') and vals.get('requisition_id'):
                vals.update({'rfc_id': self.env['purchase.requisition'].search([('id', '=', vals.get('requisition_id'))], limit=1).catalogue_rfc_id.id})
                vals.update({'catalogue_id': self.env['purchase.requisition'].search([('id', '=', vals.get('requisition_id'))], limit=1).catalogue_id.id})
                vals.update({'incoterm_id': self.env['purchase.requisition'].search([('id', '=', vals.get('requisition_id'))], limit=1).catalogue_id.incoterm_id.id})

        return super(AddisPurchaseExchangeInherited, self).create(vals_list)

    def button_confirm(self):
        # Temporary method for restricting user sending e-invoice to partner
        is_partner_e_invoice_user = False
        tenants_list_url = "http://192.168.100.209:8080/admin/v2/tenants"
        tenants_list = requests.get(tenants_list_url, timeout=TIMEOUT)
        if str(self.partner_id.name).replace(' ', '').lower() in tenants_list.json():
            is_partner_e_invoice_user = True
            if self.catalogue_id:
                try:
                    as_producer.send_new_po_request(self)
                except Exception as e:
                    _logger.warning("%s:Addis Systems Order Exchange Fail for %s", e, self.name)

        self.partner_e_invoicing = is_partner_e_invoice_user

        return super(AddisPurchaseExchangeInherited, self).button_confirm()

    def send_price_request(self):
        # send to partner for price update request
        po_send = None
        try:
            po_send = as_producer.send_po_price_request(self)
        except Exception as e:
            _logger.warning("%s:Addis Systems Order Exchange Fail for %s", e, self.name)
            self.e_ordered = False
        finally:
            if po_send:
                self.e_ordered = True
                self.state = 'sent'

    def addis_systems_catalogue_quotation_digest(self, client):
        if client:
            all_active_thread_names = [thread.name for thread in enumerate()]
            cd_thread_name = 'addis_systems_purchase_order_listener'
            if cd_thread_name not in all_active_thread_names:
                _logger.info('Starting Thread %s for company: %s', cd_thread_name, self.env.company.name)
                po_message_waiter_thread = Thread(target=consumer.purchase_order_consumer_asynch, args=(self, client), name=cd_thread_name)
                po_message_waiter_thread.daemon = True
                po_message_waiter_thread.start()
            else:
                _logger.info('Skipping Thread %s for company: %s', cd_thread_name, self.env.company.name)


class AddisPurchaseOrderLineExchangeInherited(models.Model):
    _inherit = 'purchase.order.line'

    catalogue_id = fields.Many2one(related="order_id.catalogue_id")
