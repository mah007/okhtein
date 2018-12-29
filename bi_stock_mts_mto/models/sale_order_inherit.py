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
            purchase_list = []
            purchase_order_objects = self.env['purchase.order'].sudo().search([('sale_order_id', '=', order.id)])
            purchase_order_line_objects = self.env['purchase.order.line'].sudo().search(
                [('sale_order_id', '=', order.id)])
            for purchase_order_line in purchase_order_line_objects:
                if purchase_order_line.order_id not in purchase_order_objects:
                    purchase_list.append(purchase_order_line.order_id)
            order.purchase_order_count = len(purchase_list)

            manufacture_list = []
            manufacture_order_objects = self.env['mrp.production'].sudo().search([('sale_order_id', '=', order.id)])
            production_sale_order_objects = self.env['production.sale.order'].sudo().search(
                [('sale_order_id', '=', order.id)])
            for production_line in production_sale_order_objects:
                if production_line.production_id not in manufacture_order_objects:
                    manufacture_list.append(production_line.production_id)
            order.manufacture_order_count = len(manufacture_list)

    @api.multi
    def action_view_purchase_orders(self):
        for order in self:
            purchase_list = []
            purchase_order_objects = self.env['purchase.order'].sudo().search([('sale_order_id', '=', order.id)])
            purchase_order_line_objects = self.env['purchase.order.line'].sudo().search(
                [('sale_order_id', '=', order.id)])

            for purchase_order_line in purchase_order_line_objects:
                if purchase_order_line.order_id.sale_order_id != order.id:
                    purchase_list.append(purchase_order_line.order_id.id)
            action = self.env.ref('purchase.purchase_rfq').read()[0]
            if len(purchase_list) > 1:
                action['domain'] = [('id', 'in', purchase_list)]
            elif len(purchase_list) == 1:
                action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
                action['res_id'] = purchase_list[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action

    @api.multi
    def action_view_manufacture_orders(self):
        for order in self:
            manufacture_list = []
            manufacture_order_objects = self.env['mrp.production'].sudo().search([('sale_order_id', '=', order.id)])
            production_sale_order_objects = self.env['production.sale.order'].sudo().search(
                [('sale_order_id', '=', order.id)])

            for production_line in production_sale_order_objects:
                if production_line.production_id not in manufacture_order_objects:
                    manufacture_list.append(production_line.production_id.id)
            action = self.env.ref('mrp.mrp_production_action').read()[0]
            if len(manufacture_list) > 1:
                action['domain'] = [('id', 'in', manufacture_list)]
            elif len(manufacture_list) == 1:
                action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
                action['res_id'] = manufacture_list[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action
