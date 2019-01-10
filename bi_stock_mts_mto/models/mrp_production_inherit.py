# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import math


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one('sale.order', string="Source Document", track_visibility='onchange', )
    sale_production_ids = fields.One2many('production.sale.order', 'production_id', string="Sale Orders")
    customer_reference = fields.Char(string='Customer', copy=False, readonly=True, track_visibility='onchange', )
    product_qty = fields.Float(string='Quantity To Produce', default=1.0, readonly=True, required=True,
                               track_visibility='onchange', states={'confirmed': [('readonly', False)]})

    @api.multi
    def write(self, values):
        res = super(MrpProduction, self).write(values)
        for order in self:
            if 'product_qty' in values and 'bom_id' not in values:
                for picking in order.picking_ids:
                    for move in picking.move_ids_without_package:
                        # finished product
                        if move.product_id == order.product_id:
                            if order.bom_id.product_qty == 1:
                                move.write({'product_uom_qty': values['product_qty']})
                            elif order.bom_id.product_qty > 1:
                                move.write({'product_uom_qty': values['product_qty'] / order.bom_id.product_qty})
                        # component
                        for bom_line in order.bom_id.bom_line_ids:
                            if bom_line.product_id == move.product_id:
                                if order.bom_id.product_qty == 1:
                                    move.write({'product_uom_qty': values['product_qty'] * bom_line.product_qty})
                                elif order.bom_id.product_qty > 1:
                                    move.write({'product_uom_qty': (values[
                                                                        'product_qty'] * bom_line.product_qty) / order.bom_id.product_qty})
        return res

    @api.model
    def _update_product_to_produce(self, production, qty):
        production_move = production.move_finished_ids.filtered(
            lambda x: x.product_id.id == production.product_id.id and x.state not in ('done', 'cancel'))
        if production_move:
            production_move.write({'product_uom_qty': qty})
        else:
            production_move = production._generate_finished_moves()
            production_move = production.move_finished_ids.filtered(
                lambda x: x.state not in ('done', 'cancel') and production.product_id.id == x.product_id.id)
            production_move.write({'product_uom_qty': qty})

    @api.multi
    def change_product_qty(self, qty_to_update):
        for production in self:
            qty_to_update = qty_to_update + production.product_qty
            produced = sum(production.move_finished_ids.mapped('quantity_done'))
            if qty_to_update < produced:
                raise ValidationError(
                    _("You have already processed %d. Please input a quantity higher than %d ") % (produced, produced))
            production.write({'product_qty': qty_to_update})
            done_moves = production.move_finished_ids.filtered(
                lambda x: x.state == 'done' and x.product_id == production.product_id)
            qty_produced = production.product_id.uom_id._compute_quantity(sum(done_moves.mapped('product_qty')),
                                                                          production.product_uom_id)
            factor = production.product_uom_id._compute_quantity(production.product_qty - qty_produced,
                                                                 production.bom_id.product_uom_id) / production.bom_id.product_qty
            boms, lines = production.bom_id.explode(production.product_id, factor,
                                                    picking_type=production.bom_id.picking_type_id)
            for line, line_data in lines:
                production._update_raw_move(line, line_data)
            operation_bom_qty = {}
            for bom, bom_data in boms:
                for operation in bom.routing_id.operation_ids:
                    operation_bom_qty[operation.id] = bom_data['qty']
            self._update_product_to_produce(production, production.product_qty - qty_produced)
            moves = production.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            moves._do_unreserve()
            moves._action_assign()
            for wo in production.workorder_ids:
                operation = wo.operation_id
                if operation_bom_qty.get(operation.id):
                    cycle_number = math.ceil(
                        operation_bom_qty[operation.id] / operation.workcenter_id.capacity)
                    wo.duration_expected = (operation.workcenter_id.time_start +
                                            operation.workcenter_id.time_stop +
                                            cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
                if production.product_id.tracking == 'serial':
                    quantity = 1.0
                else:
                    quantity = wo.qty_production - wo.qty_produced
                    quantity = quantity if (quantity > 0) else 0
                wo.qty_producing = quantity
                if wo.qty_produced < wo.qty_production and wo.state == 'done':
                    wo.state = 'progress'

                moves_raw = production.move_raw_ids.filtered(
                    lambda move: move.operation_id == operation and move.state not in ('done', 'cancel'))
                if wo == production.workorder_ids[-1]:
                    moves_raw |= production.move_raw_ids.filtered(lambda move: not move.operation_id)
                moves_finished = production.move_finished_ids.filtered(lambda
                                                                           move: move.operation_id == operation)
                moves_raw.mapped('move_lot_ids').write({'workorder_id': wo.id})
                (moves_finished + moves_raw).write({'workorder_id': wo.id})
                if wo.move_raw_ids.filtered(
                        lambda x: x.product_id.tracking != 'none') and not wo.active_move_lot_ids:
                    wo._generate_lot_ids()
            return {}
