from odoo import fields, models, api, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context, OrderedSet, groupby
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from collections import defaultdict
import requests
import asyncio

from .avro_schema import dispatch_schema as schema
from .addis_systems import addis_systems_producer_controller as producer
from .addis_systems import addis_systems_consumer_controller as consumer

import logging
from threading import Thread, enumerate


def check_partner_electronic_invoice_user(partner):
    tenants_list_url = "http://192.168.100.38:8080/admin/v2/tenants"
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


class AddisSystemsStockMoveInherited(models.Model):
    _inherit = 'stock.move'

    state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('on_delivery', 'On Delivery'),
        ('done', 'Done')], string='Status',
        copy=False, default='draft', index=True, readonly=True,
        help="* New: When the stock move is created and not yet confirmed.\n"
             "* Waiting Another Move: This state can be seen when a move is waiting for another one, for example in a chained flow.\n"
             "* Waiting Availability: This state is reached when the procurement resolution is not straight forward. It may need the scheduler to run, a component to be manufactured...\n"
             "* Available: When products are reserved, it is set to \'Available\'.\n"
             "* Done: When the shipment is processed, the state is \'Done\'.")

    def _action_on_delivery(self, cancel_backorder=False):
        moves = self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
        moves = (self | moves).exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_ids_todo = OrderedSet()

        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        for move in moves:
            if move.quantity_done <= 0 and not move.is_inventory:
                if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
                    move._action_cancel()

        # Create extra moves where necessary
        for move in moves:
            if move.state == 'cancel' or (move.quantity_done <= 0 and not move.is_inventory):
                continue

            moves_ids_todo |= move._create_extra_move().ids

        moves_todo = self.browse(moves_ids_todo)
        moves_todo._check_company()
        # Split moves where necessary and move quants
        backorder_moves_vals = []

        for move in moves_todo:
            # To know whether we need to create a backorder or not, round to the general product's
            # decimal precision and not the product's UOM.
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
                new_move_vals = move._split(qty_split)
                backorder_moves_vals += new_move_vals
        backorder_moves = self.env['stock.move'].create(backorder_moves_vals)

        # The backorder moves are not yet in their own picking. We do not want to check entire packs for those
        # ones as it could messed up the result_package_id of the moves being currently validated
        backorder_moves.with_context(bypass_entire_pack=True)._action_confirm(merge=False)
        if cancel_backorder:
            backorder_moves.with_context(moves_todo=moves_todo)._action_cancel()
        # moves_todo.mapped('move_line_ids').sorted()._action_done()
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo \
                .mapped('move_line_ids.result_package_id') \
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.filtered(lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity), precision_rounding=q.product_uom_id.rounding)).mapped('location_id')) > 1:
                raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        if any(ml.package_id and ml.package_id == ml.result_package_id for ml in moves_todo.move_line_ids):
            self.env['stock.quant']._unlink_zero_quants()
        picking = moves_todo.mapped('picking_id')
        moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})

        new_push_moves = moves_todo.filtered(lambda m: m.picking_id.immediate_transfer)._push_apply()
        if new_push_moves:
            new_push_moves._action_confirm()
        move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
        for move_dest in moves_todo.move_dest_ids:
            move_dests_per_company[move_dest.company_id.id] |= move_dest
        for company_id, move_dests in move_dests_per_company.items():
            move_dests.sudo().with_company(company_id)._action_assign()

        # We don't want to create back order for scrap moves
        # Replace by a kwarg in master
        if self.env.context.get('is_scrap'):
            return moves_todo

        if picking and not cancel_backorder:
            backorder = picking._create_backorder()
            if any([m.state == 'assigned' for m in backorder.move_ids]):
                backorder._check_entire_pack()
        moves_todo.write({'state': 'on_delivery', 'quantity_done': 0})
        return moves_todo


class AddisSystemsStockPicking(models.Model):
    _inherit = 'stock.picking'

    #   Override the default state and field with new and add on delivery state
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

        if all(line.quantity_done == 0 for line in self.move_ids_without_package):
            raise UserError("Quantity Done is Not set! Please set the quantity done first")
        purchase_order_id = self.env['purchase.order'].search([('name', '=', self.group_id.name)], limit=1)
        if purchase_order_id and purchase_order_id.incoterm_id.code in ['DPU', 'DAP', 'DDP'] and asyncio.run(producer.dispatch_receipt_confirm_producer(self, origin)):
            for moves in self.env['stock.move'].search([('picking_id', '=', self.id)]):
                moves.write({'state': 'done'})
        else:
            for moves in self.env['stock.move'].search([('picking_id', '=', self.id)]):
                moves.write({'state': 'done'})

        self.state = 'done'
            

    def _picking_action_on_delivery(self):
        """Call `_action_on_delivery` on the `stock.move` of the `stock.picking` in `self`.
        This method makes sure every `stock.move.line` is linked to a `stock.move` by either
        linking them to an existing one or a newly created one.

        If the context key `cancel_backorder` is present, backorders won't be created.

        :return: True
        :rtype: bool
        """
        self._check_company()

        todo_moves = self.move_ids.filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
        for picking in self:
            if picking.owner_id:
                picking.move_ids.write({'restrict_partner_id': picking.owner_id.id})
                picking.move_line_ids.write({'owner_id': picking.owner_id.id})

        todo_moves._action_on_delivery(cancel_backorder=self.env.context.get('cancel_backorder'))
        for picking in self:
            picking.state = 'on_delivery'
        return True

    def button_validate(self):
        # Clean-up the context key at validation to avoid forcing the creation of immediate
        # transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)

        # Sanity checks.
        if not self.env.context.get('skip_sanity_check', False):
            self._sanity_check()

        self.message_subscribe([self.env.user.partner_id.id])

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        pickings_not_to_backorder = self.filtered(lambda p: p.picking_type_id.create_backorder == 'never')
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder |= self.browse(self.env.context['picking_ids_not_to_backorder']).filtered(
                lambda p: p.picking_type_id.create_backorder != 'always'
            )
        pickings_to_backorder = self - pickings_not_to_backorder
        sales_order_id = self.env['sale.order'].search([('name', '=', self.group_id.name)], limit=1)
        purchase_order_id = self.env['purchase.order'].search([('name', '=', self.group_id.name)], limit=1)
        if sales_order_id and self.picking_type_id.code == "outgoing":  # AND STATE NOT ON DELIVERY
            dispatch_state = self._dispatch_advice_send_to_buyer()

            if dispatch_state['electronic_partner'] and not dispatch_state['advice_sent']:
                raise UserError("Expire Date Cannot be less than Requested Date!")
            elif dispatch_state['electronic_partner'] and dispatch_state['advice_sent']:
                self.is_advice_sent = True

            if sales_order_id.incoterm.code in ['EXW', 'FCA', 'CPT', 'CIP'] and self.is_advice_sent:
                pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
                pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

                if self.user_has_groups('stock.group_reception_report'):
                    pickings_show_report = self.filtered(lambda p: p.picking_type_id.auto_show_reception_report)
                    lines = pickings_show_report.move_ids.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
                    if lines:
                        # don't show reception report if all already assigned/nothing to assign
                        wh_location_ids = self.env['stock.location']._search([('id', 'child_of', pickings_show_report.picking_type_id.warehouse_id.view_location_id.ids), ('usage', '!=', 'supplier')])
                        if self.env['stock.move'].search([
                            ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                            ('product_qty', '>', 0),
                            ('location_id', 'in', wh_location_ids),
                            ('move_orig_ids', '=', False),
                            ('picking_id', 'not in', pickings_show_report.ids),
                            ('product_id', 'in', lines.product_id.ids)], limit=1):
                            action = pickings_show_report.action_view_reception_report()
                            action['context'] = {'default_picking_ids': pickings_show_report.ids}
                            return action
                return True
            elif sales_order_id.incoterm.code in ['DPU', 'DAP', 'DDP'] and self.is_advice_sent:
                pickings_not_to_backorder.with_context(cancel_backorder=True)._picking_action_on_delivery()
                pickings_to_backorder.with_context(cancel_backorder=False)._picking_action_on_delivery()

                if self.user_has_groups('stock.group_reception_report'):
                    pickings_show_report = self.filtered(lambda p: p.picking_type_id.auto_show_reception_report)
                    lines = pickings_show_report.move_ids.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
                    if lines:
                        # don't show reception report if all already assigned/nothing to assign
                        wh_location_ids = self.env['stock.location']._search([('id', 'child_of', pickings_show_report.picking_type_id.warehouse_id.view_location_id.ids), ('usage', '!=', 'supplier')])
                        if self.env['stock.move'].search([
                            ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                            ('product_qty', '>', 0),
                            ('location_id', 'in', wh_location_ids),
                            ('move_orig_ids', '=', False),
                            ('picking_id', 'not in', pickings_show_report.ids),
                            ('product_id', 'in', lines.product_id.ids)], limit=1):
                            action = pickings_show_report.action_view_reception_report()
                            action['context'] = {'default_picking_ids': pickings_show_report.ids}
                            return action
                return True
            else:
                pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
                pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

                if self.user_has_groups('stock.group_reception_report'):
                    pickings_show_report = self.filtered(lambda p: p.picking_type_id.auto_show_reception_report)
                    lines = pickings_show_report.move_ids.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
                    if lines:
                        # don't show reception report if all already assigned/nothing to assign
                        wh_location_ids = self.env['stock.location']._search([('id', 'child_of', pickings_show_report.picking_type_id.warehouse_id.view_location_id.ids), ('usage', '!=', 'supplier')])
                        if self.env['stock.move'].search([
                            ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                            ('product_qty', '>', 0),
                            ('location_id', 'in', wh_location_ids),
                            ('move_orig_ids', '=', False),
                            ('picking_id', 'not in', pickings_show_report.ids),
                            ('product_id', 'in', lines.product_id.ids)], limit=1):
                            action = pickings_show_report.action_view_reception_report()
                            action['context'] = {'default_picking_ids': pickings_show_report.ids}
                            return action
                return True
        elif purchase_order_id and self.picking_type_id.code == "incoming":
            is_electronic = check_partner_electronic_invoice_user(self.partner_id)
            if is_electronic and purchase_order_id.partner_e_invoicing:
                pickings_not_to_backorder.with_context(cancel_backorder=True)._picking_action_on_delivery()
                pickings_to_backorder.with_context(cancel_backorder=False)._picking_action_on_delivery()

                if self.user_has_groups('stock.group_reception_report'):
                    pickings_show_report = self.filtered(lambda p: p.picking_type_id.auto_show_reception_report)
                    lines = pickings_show_report.move_ids.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
                    if lines:
                        # don't show reception report if all already assigned/nothing to assign
                        wh_location_ids = self.env['stock.location']._search([('id', 'child_of', pickings_show_report.picking_type_id.warehouse_id.view_location_id.ids), ('usage', '!=', 'supplier')])
                        if self.env['stock.move'].search([
                            ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                            ('product_qty', '>', 0),
                            ('location_id', 'in', wh_location_ids),
                            ('move_orig_ids', '=', False),
                            ('picking_id', 'not in', pickings_show_report.ids),
                            ('product_id', 'in', lines.product_id.ids)], limit=1):
                            action = pickings_show_report.action_view_reception_report()
                            action['context'] = {'default_picking_ids': pickings_show_report.ids}
                            return action
                return True
        else:
            pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
            pickings_to_backorder.with_context(cancel_backorder=False)._action_done()

            if self.user_has_groups('stock.group_reception_report'):
                pickings_show_report = self.filtered(lambda p: p.picking_type_id.auto_show_reception_report)
                lines = pickings_show_report.move_ids.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity_done and not m.move_dest_ids)
                if lines:
                    # don't show reception report if all already assigned/nothing to assign
                    wh_location_ids = self.env['stock.location']._search([('id', 'child_of', pickings_show_report.picking_type_id.warehouse_id.view_location_id.ids), ('usage', '!=', 'supplier')])
                    if self.env['stock.move'].search([
                        ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                        ('product_qty', '>', 0),
                        ('location_id', 'in', wh_location_ids),
                        ('move_orig_ids', '=', False),
                        ('picking_id', 'not in', pickings_show_report.ids),
                        ('product_id', 'in', lines.product_id.ids)], limit=1):
                        action = pickings_show_report.action_view_reception_report()
                        action['context'] = {'default_picking_ids': pickings_show_report.ids}
                        return action
            return True

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
