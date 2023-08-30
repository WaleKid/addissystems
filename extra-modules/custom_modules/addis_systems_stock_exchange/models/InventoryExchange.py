from odoo import fields, models, api, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError
from collections import defaultdict
import requests
import asyncio

from .avro_schema import dispatch_schema as schema
from .addis_systems import addis_systems_producer_controller as producer
from .addis_systems import addis_systems_consumer_controller as consumer

import logging
from threading import Thread, enumerate


def check_partner_electronic_invoice_user(partner):
    tenants_list_url = "http://196.189.124.178:8080/admin/v2/tenants"
    tenants_list = requests.get(tenants_list_url, timeout=150)
    return str(partner.name).replace(' ', '').lower() in tenants_list.json()


_logger = logging.getLogger(__name__)


class AddisBaseStockExchangeInherited(models.Model):
    _inherit = 'res.company'

    def addis_system_connection_init(self):
        super(AddisBaseStockExchangeInherited, self).addis_system_connection_init()
        # Stock Receipt Consumer Caller
        self.env['stock.picking'].addis_systems_inventory_receipt_digest()
        # Stock Delivery Confirmation Consumer Caller
        self.env['stock.picking'].addis_systems_inventory_delivery_confirmations_digest()


class AddisSystemsStockPicking(models.Model):
    _inherit = 'stock.picking'

    #   Override the default state and field with new and add on delivery state
    # state = fields.Selection(selection_add=[('on_delivery', 'On Delivery')], ondelete={'dispatch': 'cascade'})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('on_delivery', 'On Delivery'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

    # Dispatch Advice state
    dispatch_reference_number = fields.Char(string="Dispatch Reference", required=False, translate=True)
    is_advice_sent = fields.Boolean(string="Dispatch Advise Sent", default=False)
    picking_type = fields.Selection(related='picking_type_id.code', string="Picking Operation Type")

    @api.depends('move_type', 'immediate_transfer', 'move_ids.state', 'move_ids.picking_id')
    def _compute_state(self):
        ''' State of a picking depends on the state of its related stock.move
        - Draft: only used for "planned pickings"
        - Waiting: if the picking is not ready to be sent so if
          - (a) no quantity could be reserved at all or if
          - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
        - Waiting another move: if the picking is waiting for another move
        - Ready: if the picking is ready to be sent so if:
          - (a) all quantities are reserved or if
          - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
        - Done: if the picking is done.
        - Cancelled: if the picking is cancelled
        '''
        picking_moves_state_map = defaultdict(dict)
        picking_move_lines = defaultdict(set)
        for move in self.env['stock.move'].search([('picking_id', 'in', self.ids)]):
            picking_id = move.picking_id
            move_state = move.state
            picking_moves_state_map[picking_id.id].update({
                'any_draft': picking_moves_state_map[picking_id.id].get('any_draft', False) or move_state == 'draft',
                'all_cancel': picking_moves_state_map[picking_id.id].get('all_cancel', True) and move_state == 'cancel',
                'all_cancel_done': picking_moves_state_map[picking_id.id].get('all_cancel_done', True) and move_state in ('cancel', 'done'),
                'all_done_are_scrapped': picking_moves_state_map[picking_id.id].get('all_done_are_scrapped', True) and (move.scrapped if move_state == 'done' else True),
                'any_cancel_and_not_scrapped': picking_moves_state_map[picking_id.id].get('any_cancel_and_not_scrapped', False) or (move_state == 'cancel' and not move.scrapped),
            })
            picking_move_lines[picking_id.id].add(move.id)
        for picking in self:
            picking_id = (picking.ids and picking.ids[0]) or picking.id
            if not picking_moves_state_map[picking_id]:
                picking.state = 'draft'
            elif picking_moves_state_map[picking_id]['any_draft']:
                picking.state = 'draft'
            elif picking_moves_state_map[picking_id]['all_cancel']:
                picking.state = 'cancel'
            elif picking_moves_state_map[picking_id]['all_cancel_done']:
                if picking_moves_state_map[picking_id]['all_done_are_scrapped'] and picking_moves_state_map[picking_id]['any_cancel_and_not_scrapped']:
                    picking.state = 'cancel'
                else:
                    if picking.picking_type == 'outgoing':
                        dispatch_state = None
                        # To Handle the Dispatch Note and Advice
                        if not picking.is_advice_sent:
                            dispatch_state = picking._dispatch_advice_send_to_buyer()

                        if not dispatch_state['electronic_partner']:
                            # Partner is not electronic user consider picking is done
                            picking.state = 'done'
                        elif dispatch_state['electronic_partner'] and not dispatch_state['advice_sent']:
                            # Partner is electronic user but the dispatch advice couldn't be processed consider picking is still on assigned
                            picking.state = 'assigned'
                        elif dispatch_state['electronic_partner'] and dispatch_state['advice_sent']:
                            # Partner is electronic user and dispatch advise is sent
                            picking.state = 'on_delivery'
                            # Reverse the quantity_done to 0
                    elif picking.picking_type == 'incoming':
                        picking.state = 'on_delivery'
            else:
                relevant_move_state = self.env['stock.move'].browse(picking_move_lines[picking_id])._get_relevant_state_among_moves()
                if picking.immediate_transfer and relevant_move_state not in ('draft', 'cancel', 'done'):
                    picking.state = 'assigned'
                elif relevant_move_state == 'partially_available':
                    picking.state = 'assigned'
                else:
                    picking.state = relevant_move_state

    def _dispatch_advice_send_to_buyer(self):
        origin = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
        is_electronic = check_partner_electronic_invoice_user(self.partner_id)
        if not is_electronic:
            return {'electronic_partner': False, 'advice_sent': False}
        self.dispatch_reference_number = self.env['ir.sequence'].next_by_code('stock.dispatch') or _('New')
        if asyncio.run(producer.dispatch_producer(self, origin)):
            return {'electronic_partner': True, 'advice_sent': True}

        return {'electronic_partner': True, 'advice_sent': False}

    def confirm_inventory_receipt(self):
        origin = self.env['purchase.order'].search([('name', '=', self.origin)], limit=1)
        if asyncio.run(producer.dispatch_receipt_confirm_producer(self, origin)):
            self.state = 'done'

    def addis_systems_inventory_receipt_digest(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        stock_receipt_thread_name = 'addis_systems_stock_transfer_receipt_listener'
        if stock_receipt_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', stock_receipt_thread_name, self.env.company.name)
            stock_receipt_message_waiter_thread = Thread(target=consumer.stock_receipt_consumer_asynch, args=(self, stock_receipt_thread_name), name=stock_receipt_thread_name)
            stock_receipt_message_waiter_thread.daemon = True
            stock_receipt_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', stock_receipt_thread_name, self.env.company.name)

    def addis_systems_inventory_delivery_confirmations_digest(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        stock_delivery_confirmation_thread_name = 'addis_systems_stock_transfer_delivery_confirmation_listener'
        if stock_delivery_confirmation_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', stock_delivery_confirmation_thread_name, self.env.company.name)
            stock_delivery_confirmation_message_waiter_thread = Thread(target=consumer.stock_delivery_confirmation_consumer_asynch, args=(self, stock_delivery_confirmation_thread_name), name=stock_delivery_confirmation_thread_name)
            stock_delivery_confirmation_message_waiter_thread.daemon = True
            stock_delivery_confirmation_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', stock_delivery_confirmation_thread_name, self.env.company.name)
