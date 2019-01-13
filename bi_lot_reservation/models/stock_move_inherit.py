from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_compare


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    @api.depends('lot_id')
    def get_lot_on_hand_qty(self):
        for move_line in self:
            total_on_hand_qty = 0
            operation = self.env['stock.move'].browse(move_line.move_id.id)
            if operation.picking_id.picking_type_id.default_location_src_id and move_line.lot_id:
                product_quants_objects = self.env['stock.quant'].search(
                    [('product_id', '=', operation.product_id.id), ('lot_id', '=', move_line.lot_id.id), (
                        'location_id', '=', operation.picking_id.picking_type_id.default_location_src_id.id)])
                for product_quant in product_quants_objects:
                    total_on_hand_qty += product_quant.qty
                move_line.product_lot_on_hand_qty = total_on_hand_qty
            else:
                move_line.product_lot_on_hand_qty = 0

    product_lot_on_hand_qty = fields.Float(compute="get_lot_on_hand_qty", string='Lot Qty On Hand', readonly=True)

    @api.constrains('qty_done')
    def check_on_hand_qty(self):
        for move_line in self:
            if move_line.move_id.picking_id.picking_type_id.code != 'incoming' and move_line.lot_id:
                if move_line.qty_done > move_line.product_lot_on_hand_qty:
                    raise ValidationError(
                        "You cannot proceed more than quantity on hand for lot: %s" % move_line.lot_id.name)


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    @api.constrains('move_line_ids')
    def check_done_qty(self):
        for record in self:
            if record.move_line_ids:
                total_done = sum(record.move_line_ids.mapped('qty_done'))
                if total_done > record.product_uom_qty:
                    raise ValidationError(_('Total qty done must equal ' + str(record.product_uom_qty)))
