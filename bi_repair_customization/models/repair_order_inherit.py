# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    receive_date = fields.Date(string="Received Date", )
    finish_date = fields.Date(string="Finished Date", )
    location_id = fields.Many2one('stock.location', string='Delivered Location', required=True, index=False,
                                  default=False,
                                  states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]})

    destination_location_id = fields.Many2one('stock.location', string='Destination Location', required=True,
                                              default=False, states={'draft': [('readonly', False)],
                                                                     'confirmed': [('readonly', True)]})
    receipt_source_location_id = fields.Many2one('stock.location', string='Source Location (Receipt)', required=True,
                                                 default=False, states={'draft': [('readonly', False)],
                                                                        'confirmed': [('readonly', True)]})
    receipt_destination_location_id = fields.Many2one('stock.location', string='Destination Location (Receipt)',
                                                      required=True, default=False,
                                                      states={'draft': [('readonly', False)],
                                                              'confirmed': [('readonly', True)]})
    receipt_stock_picking_id = fields.Many2one('stock.picking', 'Receipt', copy=False, readonly=True)
    delivery_stock_picking_id = fields.Many2one('stock.picking', 'Delivery', copy=False, readonly=True)

    @api.constrains('receive_date', 'finish_date')
    def check_repair_order_dates(self):
        for order in self:
            if order.finish_date and order.receive_date:
                if order.receive_date > order.finish_date:
                    raise ValidationError(_('Order received date must be less than order finished date.'))

    @api.onchange('receipt_source_location_id')
    def set_destination_location(self):
        for order in self:
            if order.receipt_source_location_id:
                order.destination_location_id = order.receipt_source_location_id.id

    @api.onchange('receipt_destination_location_id')
    def set_location(self):
        for order in self:
            if order.receipt_destination_location_id:
                order.location_id = order.receipt_destination_location_id.id

    @api.multi
    def action_validate(self):
        return self.action_repair_confirm()

    @api.multi
    def action_repair_confirm(self):
        stock_picking_type_id = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming')], limit=1).id
        for order in self:
            if not stock_picking_type_id:
                raise ValidationError(_('Please configure receipt picking type for your company.'))
            picking_vals = {
                'origin': order.name,
                'partner_id': order.partner_id.id,
                'scheduled_date': fields.Datetime.now(),
                'picking_type_id': stock_picking_type_id,
                'location_id': order.receipt_source_location_id.id,
                'location_dest_id': order.receipt_destination_location_id.id,
                'company_id': order.company_id.id,
                'move_type': 'direct',
                'state': 'waiting',
            }
            created_picking_object = self.env['stock.picking'].create(picking_vals)
            created_move_object = self.env['stock.move'].create({
                'product_id': order.product_id.id,
                'name': order.product_id.name,
                'product_uom_qty': order.product_qty,
                'product_uom': order.product_uom.id,
                'company_id': order.company_id.id,
                'location_id': order.receipt_source_location_id.id,
                'location_dest_id': order.receipt_destination_location_id.id,
                'picking_id': created_picking_object.id,
            })

            order.write({'state': 'confirmed', 'receipt_stock_picking_id': created_picking_object.id})

    @api.multi
    def action_repair_end(self):
        stock_picking_type_id = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing')], limit=1).id
        for order in self:
            if not stock_picking_type_id:
                raise ValidationError(_('Please configure delivery picking type for your company.'))
            picking_vals = {
                'origin': order.name,
                'partner_id': order.partner_id.id,
                'scheduled_date': fields.Datetime.now(),
                'picking_type_id': stock_picking_type_id,
                'location_id': order.location_id.id,
                'location_dest_id': order.destination_location_id.id,
                'company_id': order.company_id.id,
                'move_type': 'direct',
                'state': 'waiting',
            }
            created_picking_object = self.env['stock.picking'].create(picking_vals)
            created_move_object = self.env['stock.move'].create({
                'product_id': order.product_id.id,
                'name': order.product_id.name,
                'product_uom_qty': order.product_qty,
                'product_uom': order.product_uom.id,
                'company_id': order.company_id.id,
                'location_id': order.location_id.id,
                'location_dest_id': order.destination_location_id.id,
                'picking_id': created_picking_object.id,
            })

            order.write({'state': 'done', 'delivery_stock_picking_id': created_picking_object.id})
