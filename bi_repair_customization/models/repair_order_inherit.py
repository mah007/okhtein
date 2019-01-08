# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    receive_date = fields.Date(string="Received Date")
    finish_date = fields.Date(string="Finished Date")
    location_id = fields.Many2one(
        'stock.location', 'Delivered Location',
        index=True, readonly=True, required=True,
        help="This is the location where the product to repair is located.",
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})
    location_destination = fields.Many2one(
        'stock.location', 'Destination Location',
        index=True, required=True)
    source_location = fields.Many2one(
        'stock.location', 'Source Location (Receipt)',
        index=True, required=True)
    destination_location = fields.Many2one(
        'stock.location', 'Destination Location (Receipt)',
        index=True, required=True)
    confirm_id = fields.Many2one(
        'stock.move', 'To confirm',
        copy=False, readonly=True)

    @api.constrains('receive_date', 'finish_date')
    def check_repair_order_dates(self):
        for order in self:
            if order.finish_date and order.receive_date:
                if order.receive_date > order.finish_date:
                    raise ValidationError(_('Order received date must be less than order finished date.'))

    @api.multi
    def action_repair_confirm(self):
        if self.filtered(lambda repair: repair.state != 'draft'):
            raise UserError(_("Repair must be under repair in order to end reparation."))
        for repair in self:
            repair.write({'repaired': True})
            vals = {'state': 'draft'}
            vals['confirm_id'] = repair.action_confirm_done().get(repair.id)
            if not repair.invoiced and repair.invoice_method == 'after_repair':
                vals['state'] = '2binvoiced'
            repair.write(vals)

        before_repair = self.filtered(lambda repair: repair.invoice_method == 'b4repair')
        before_repair.write({'state': '2binvoiced'})
        to_confirm = self - before_repair
        to_confirm_operations = to_confirm.mapped('operations')
        to_confirm_operations.write({'state': 'confirmed'})
        to_confirm.write({'state': 'confirmed'})
        return True

    @api.multi
    def action_confirm_done(self):
        res = {}
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        Move = self.env['stock.move']
        for repair in self:
            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id, repair.location_id,
                                                                                  repair.lot_id,
                                                                                  owner_id=repair.partner_id,
                                                                                  strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id

            moves = self.env['stock.move']
            for operation in repair.operations:
                move = Move.create({
                    'name': repair.name,
                    'product_id': operation.product_id.id,
                    'product_uom_qty': operation.product_uom_qty,
                    'product_uom': operation.product_uom.id,
                    'partner_id': repair.address_id.id,
                    'location_id': operation.location_id.id,
                    'location_dest_id': operation.location_dest_id.id,
                    'move_line_ids': [(0, 0, {'product_id': operation.product_id.id,
                                              'lot_id': operation.lot_id.id,
                                              'product_uom_qty': 0,  # bypass reservation here
                                              'product_uom_id': operation.product_uom.id,
                                              'qty_done': operation.product_uom_qty,
                                              'package_id': False,
                                              'result_package_id': False,
                                              'owner_id': owner_id,
                                              'location_id': operation.location_id.id,  # TODO: owner stuff
                                              'location_dest_id': operation.location_dest_id.id, })],
                    'repair_id': repair.id,
                    'origin': repair.name,
                })
                moves |= move
                operation.write({'confirm_id': move.id, 'state': 'draft'})
            move = Move.create({
                'name': repair.name,
                'product_id': repair.product_id.id,
                'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                'product_uom_qty': repair.product_qty,
                'partner_id': repair.address_id.id,
                'location_id': repair.source_location.id,
                'location_dest_id': repair.destination_location.id,
                'move_line_ids': [(0, 0, {'product_id': repair.product_id.id,
                                          'lot_id': repair.lot_id.id,
                                          'product_uom_qty': 0,  # bypass reservation here
                                          'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                                          'qty_done': repair.product_qty,
                                          'package_id': False,
                                          'result_package_id': False,
                                          'owner_id': owner_id,
                                          'location_id': repair.source_location.id,  # TODO: owner stuff
                                          'location_dest_id': repair.destination_location.id, })],
                'repair_id': repair.id,
                'origin': repair.name,
            })
            consumed_lines = moves.mapped('move_line_ids')
            produced_lines = move.move_line_ids
            moves |= move
            moves._action_done()
            produced_lines.write({'consume_line_ids': [(6, 0, consumed_lines.ids)]})
            res[repair.id] = move.id
        return res

    @api.multi
    def action_repair_done(self):
        if self.filtered(lambda repair: not repair.repaired):
            raise UserError(_("Repair must be repaired in order to make the product moves."))
        res = {}
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        Move = self.env['stock.move']
        for repair in self:
            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id, repair.location_id,
                                                                                  repair.lot_id,
                                                                                  owner_id=repair.partner_id,
                                                                                  strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id

            moves = self.env['stock.move']
            for operation in repair.operations:
                move = Move.create({
                    'name': repair.name,
                    'product_id': operation.product_id.id,
                    'product_uom_qty': operation.product_uom_qty,
                    'product_uom': operation.product_uom.id,
                    'partner_id': repair.address_id.id,
                    'location_id': operation.location_id.id,
                    'location_dest_id': operation.location_dest_id.id,
                    'move_line_ids': [(0, 0, {'product_id': operation.product_id.id,
                                              'lot_id': operation.lot_id.id,
                                              'product_uom_qty': 0,  # bypass reservation here
                                              'product_uom_id': operation.product_uom.id,
                                              'qty_done': operation.product_uom_qty,
                                              'package_id': False,
                                              'result_package_id': False,
                                              'owner_id': owner_id,
                                              'location_id': operation.location_id.id,  # TODO: owner stuff
                                              'location_dest_id': operation.location_dest_id.id, })],
                    'repair_id': repair.id,
                    'origin': repair.name,
                })
                moves |= move
                operation.write({'move_id': move.id, 'state': 'done'})
            move = Move.create({
                'name': repair.name,
                'product_id': repair.product_id.id,
                'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                'product_uom_qty': repair.product_qty,
                'partner_id': repair.address_id.id,
                'location_id': repair.location_id.id,
                'location_dest_id': repair.location_destination.id,
                'move_line_ids': [(0, 0, {'product_id': repair.product_id.id,
                                          'lot_id': repair.lot_id.id,
                                          'product_uom_qty': 0,  # bypass reservation here
                                          'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                                          'qty_done': repair.product_qty,
                                          'package_id': False,
                                          'result_package_id': False,
                                          'owner_id': owner_id,
                                          'location_id': repair.location_id.id,  # TODO: owner stuff
                                          'location_dest_id': repair.location_destination.id, })],
                'repair_id': repair.id,
                'origin': repair.name,
            })
            consumed_lines = moves.mapped('move_line_ids')
            produced_lines = move.move_line_ids
            moves |= move
            moves._action_done()
            produced_lines.write({'consume_line_ids': [(6, 0, consumed_lines.ids)]})
            res[repair.id] = move.id
        return res
