# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    project_name = fields.Char(string='Project')
    customer_po = fields.Char(string='Customer PO')
    purchase_order_count = fields.Integer(string='No Of Purchases', compute='get_order_count')
    manufacture_order_count = fields.Integer(string='No Of Manufactures', compute='get_order_count')

    @api.multi
    def get_order_count(self):
        for order in self:
            purchase_list = manufacture_list = []
            purchase_order_objects = self.env['purchase.order'].sudo().search([('sale_order_id', '=', order.id)])
            purchase_order_line_objects = self.env['purchase.order.line'].sudo().search(
                [('sale_order_id', '=', order.id)])
            manufacture_order_objects = self.env['mrp.production'].sudo().search([('sale_order_id', '=', order.id)])
            production_sale_order_objects = self.env['production.sale.order'].sudo().search(
                [('sale_order_id', '=', order.id)])

            for purchase_order_line in purchase_order_line_objects:
                if purchase_order_line.order_id not in purchase_order_objects:
                    purchase_list += purchase_order_line.order_id

            for production_line in production_sale_order_objects:
                if production_line.production_id not in manufacture_order_objects:
                    manufacture_list += production_line.production_id
            order.purchase_order_count = len(purchase_list)
            order.manufacture_order_count = len(manufacture_list)

    @api.multi
    def action_view_purchase_orders(self):
        print ("action_view_purchase_orders")
    #     for order in self:
    #         purchase_list = manufacture_list = []
    #         purchase_order_objects = self.env['purchase.order'].sudo().search([('sale_order_id', '=', order.id)])
    #         purchase_order_line_objects = self.env['purchase.order.line'].sudo().search(
    #             [('sale_order_id', '=', order.id)])
    #         for purchase_order_line in purchase_order_line_objects:
    #             if purchase_order_line.sale_order_id.sale_production_id == order.id and not :
    #                 purchases += line.order_id
    #         print ("purchase_order_objects", purchase_order_objects)
    #         action = self.env.ref('purchase.purchase_rfq').read()[0]
    #         action['domain'] = [('id', 'in', purchase_list)]
    #         return action

    @api.multi
    def action_view_manufacture_orders(self):
        print ("action_view_manufacture_orders")
        # manufactures = self.env['mrp.production'].sudo().search([('sale_production_id', '=', self.id)])
        # manufacture_lines = self.env['production.sale.order'].sudo().search([('sale_order_id', '=', self.id)])
        # for line in manufacture_lines:
        #     if line.production_id not in manufactures:
        #         manufactures += line.production_id
        # action = self.env.ref('mrp.mrp_production_action').read()[0]
        # if len(manufactures) > 1:
        #     action['domain'] = [('id', 'in', manufactures.ids)]
        # elif len(manufactures) == 1:
        #     action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
        #     action['res_id'] = manufactures.ids[0]
        # else:
        #     action = {'type': 'ir.actions.act_window_close'}
        # return action
