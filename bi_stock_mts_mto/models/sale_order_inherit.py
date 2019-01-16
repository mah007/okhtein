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
            purchase_order_objects = self.env['purchase.order'].sudo().search([('sale_order_id', '=', order.id)])
            purchase_order_line_objects = self.env['purchase.order.line'].sudo().search(
                [('sale_order_id', '=', order.id)])
            for purchase_order_line in purchase_order_line_objects:

                if purchase_order_line.order_id not in purchase_order_objects:
                    purchase_order_objects += purchase_order_line.order_id
            order.purchase_order_count = len(purchase_order_objects)

            manufacture_order_objects = self.env['mrp.production'].sudo().search([('sale_order_id', '=', order.id)])
            production_sale_order_objects = self.env['production.sale.order'].sudo().search(
                [('sale_order_id', '=', order.id)])
            for production_line in production_sale_order_objects:
                if production_line.production_id not in manufacture_order_objects:
                    manufacture_order_objects += production_line.production_id

            order.manufacture_order_count = len(manufacture_order_objects)

    @api.multi
    def action_view_purchase_orders(self):
        for order in self:
            purchase_order_objects = self.env['purchase.order'].sudo().search([('sale_order_id', '=', order.id)])
            purchase_order_line_objects = self.env['purchase.order.line'].sudo().search(
                [('sale_order_id', '=', order.id)])

            for purchase_order_line in purchase_order_line_objects:
                if purchase_order_line.order_id.sale_order_id != order.id:
                    purchase_order_objects += purchase_order_line.order_id

            action = self.env.ref('purchase.purchase_rfq').read()[0]
            if len(purchase_order_objects) > 1:
                action['domain'] = [('id', 'in', purchase_order_objects.ids)]
            elif len(purchase_order_objects) == 1:
                action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
                action['res_id'] = purchase_order_objects[0].id
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action

    @api.multi
    def action_view_manufacture_orders(self):
        for order in self:
            manufacture_order_objects = self.env['mrp.production'].sudo().search([('sale_order_id', '=', order.id)])
            production_sale_order_objects = self.env['production.sale.order'].sudo().search(
                [('sale_order_id', '=', order.id)])

            for production_line in production_sale_order_objects:
                if production_line.production_id not in manufacture_order_objects:
                    manufacture_order_objects += production_line.production_id

            action = self.env.ref('mrp.mrp_production_action').read()[0]
            if len(manufacture_order_objects) > 1:
                action['domain'] = [('id', 'in', manufacture_order_objects.ids)]
            elif len(manufacture_order_objects) == 1:
                action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
                action['res_id'] = manufacture_order_objects[0].id
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action

    @api.multi
    def get_procurement_method(self, product_id):
        procurement_method = ''
        is_mts = False
        for route in product_id.route_ids:
            for rule in route.rule_ids:
                if rule.action == 'buy':
                    procurement_method = 'buy'
                elif rule.action == 'manufacture':
                    procurement_method = 'manufacture'
        for route in product_id.route_ids:
            if route.is_mts:
                return procurement_method

    @api.multi
    def get_order_virtual_quantity(self, product_id, qty, from_mo=False):
        if from_mo:
            mo_virtual_qty = product_id.virtual_available + qty
            if mo_virtual_qty < 0:
                virtual_qty = 0
            else:
                virtual_qty = mo_virtual_qty
        else:
            if product_id.virtual_available < 0:
                virtual_qty = 0
            else:
                virtual_qty = product_id.virtual_available
        return virtual_qty

    @api.multi
    def create_po_procurement_order(self, product_id, qty, from_mo=False):
        for vendor in product_id.seller_ids:
            virtual_qty = self.get_order_virtual_quantity(product_id, qty, from_mo)
            rfq = self.env['purchase.order'].sudo().search(
                [('partner_id', '=', vendor.name.id), ('state', '=', 'draft')],
                order="id desc", limit=1)
            if product_id.description_sale:
                product_desc = product_id.description_sale
            else:
                product_desc = product_id.name
            origin = self.name + ": Buy -> CustomersMTO"
            if rfq:
                rfq.write({'origin': origin})
                created_purchase_order_line = self.env['purchase.order.line'].sudo().create(
                    {'product_id': product_id.id,
                     'product_qty': qty - virtual_qty,
                     'product_uom': product_id.uom_id.id,
                     'price_unit': product_id.standard_price,
                     'name': product_desc,
                     'date_planned': fields.Datetime.now(),
                     'order_id': rfq.id
                     })
                created_purchase_order_line.write({'sale_order_id': self.id, })
            else:
                seq_id = self.env['ir.sequence'].search(
                    [('code', '=', 'purchase.order'), ('company_id', '=', self.company_id.id)]).id
                seq = 'New'
                if seq_id:
                    seq = self.env['ir.sequence'].get_id(seq_id)
                type_obj = self.env['stock.picking.type']
                types = type_obj.search(
                    [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', self.company_id.id)])
                if not types:
                    types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
                created_purchase_order = self.env['purchase.order'].sudo().create({
                    'partner_id': vendor.name.id,
                    'origin': origin,
                    'name': seq,
                    'sale_order_id': self.id,
                    'company_id': self.company_id.id,
                    'picking_type_id': types[:1].id,
                })
                created_purchase_order_line = self.env['purchase.order.line'].sudo().create(
                    {'product_id': product_id.id,
                     'product_qty': qty - virtual_qty,
                     'product_uom': product_id.uom_id.id,
                     'price_unit': product_id.standard_price,
                     'name': product_desc,
                     'date_planned': fields.Datetime.now(),
                     'order_id': created_purchase_order.id
                     })
                created_purchase_order_line.write({'sale_order_id': self.id, })

    @api.multi
    def action_confirm(self):
        for order in self:
            product_grouped_dict = {}
            for line in order.order_line:
                if line.product_id in product_grouped_dict:
                    product_grouped_dict[line.product_id]['qty'] += line.product_uom_qty
                else:
                    product_grouped_dict[line.product_id] = {'qty': line.product_uom_qty}
            for product in product_grouped_dict:
                if product_grouped_dict[product]['qty'] > product.virtual_available:
                    procurement_method = order.get_procurement_method(product)
                    if procurement_method == 'buy':
                        order.create_po_procurement_order(product, product_grouped_dict[product]['qty'])
                    elif procurement_method == 'manufacture':
                        order.create_mo_procurement_order(product, product_grouped_dict[product]['qty'])
        return super(SaleOrder, self).action_confirm()

    @api.multi
    def create_mo_procurement_order(self, product_id, qty, from_mo=False):
        virtual_qty = self.get_order_virtual_quantity(product_id, qty, from_mo)
        product_bom_id = self.env['mrp.bom'].sudo().search([('product_id', '=', product_id.id)], order="id desc",
                                                           limit=1)
        prod_id = product_bom_id
        produc_tmpl_bom_id = self.env['mrp.bom'].sudo().search(
            [('product_tmpl_id', '=', product_id.product_tmpl_id.id)], order="id desc", limit=1)

        if product_bom_id:
            prod_id = product_bom_id
        elif produc_tmpl_bom_id:
            prod_id = produc_tmpl_bom_id

        if prod_id:
            ref = self.name + ":Manufacture -> CustomersMTO"
            customer = self.partner_id.name
            mrp = self.env['mrp.production'].search(
                [('product_id', '=', product_id.id), ('company_id', '=', self.company_id.id),
                 ('state', '=', 'confirmed')], limit=1)
            if mrp:
                mrp.change_product_qty(qty - virtual_qty)
                add_source = True
                add_customer = True
                for sale_id in mrp.sale_production_ids:
                    if sale_id.sale_order_id.id == self.id:
                        add_source = False
                        add_customer = False
                if mrp.origin and add_source:
                    ref = mrp.origin + ', ' + ref
                if mrp.customer_reference and add_customer:
                    customer = mrp.customer_reference + ', ' + customer
            else:
                picking_type_id = self.env['stock.picking.type'].sudo().search(
                    [('code', '=', 'mrp_operation'), ('warehouse_id.company_id', '=', self.company_id.id)], limit=1)
                seq_id = self.env['ir.sequence'].sudo().search(
                    [('code', '=', 'mrp.production'), ('company_id', '=', self.company_id.id)]).id
                seq = 'New'
                if seq_id:
                    seq = self.env['ir.sequence'].get_id(seq_id)
                mrp = self.env['mrp.production'].sudo().create({
                    'product_id': product_id.id,
                    'product_qty': qty - virtual_qty,
                    'product_uom_id': product_id.uom_id.id,
                    'bom_id': prod_id.id,
                    'name': seq,
                    'company_id': self.company_id.id,
                    'picking_type_id': prod_id.picking_type_id.id if prod_id.picking_type_id.id else picking_type_id.id,
                    'sale_order_id': self.id,
                    'location_src_id': prod_id.picking_type_id.default_location_src_id.id if prod_id.picking_type_id.default_location_src_id.id else picking_type_id.default_location_src_id.id,
                    'location_dest_id': prod_id.picking_type_id.default_location_dest_id.id if prod_id.picking_type_id.default_location_dest_id.id else picking_type_id.default_location_dest_id.id,
                })
            if mrp:
                sale_production_vals = {'sale_order_id': self.id, 'status': 'sale', 'ordered_qty': qty,
                                        'avail_qty': virtual_qty,
                                        'qty_to_produce': qty - virtual_qty,
                                        'production_id': mrp.id
                                        }
                mrp.write(
                    {'origin': ref, 'customer_reference': customer,
                     'sale_production_ids': [(0, 0, sale_production_vals)]})

                for mrp_line in mrp.move_raw_ids:
                    virtual_qty = self.get_order_virtual_quantity(mrp_line.product_id, mrp_line.product_uom_qty, True)
                    if mrp_line.product_uom_qty > virtual_qty:
                        procurement_method = self.get_procurement_method(mrp_line.product_id)
                        if procurement_method == 'buy':
                            self.create_po_procurement_order(mrp_line.product_id, mrp_line.product_uom_qty, True)
                        elif procurement_method == 'manufacture':
                            self.create_mo_procurement_order(mrp_line.product_id, mrp_line.product_uom_qty, True)

    @api.multi
    def action_done(self):
        for order in self:
            for production_sale_order in self.env['production.sale.order'].sudo().search(
                    [('sale_order_id', '=', order.id), ('status', '!=', 'cancel')]):
                production_sale_order.write({'status': 'locked'})
        return super(SaleOrder, self).action_done()

    @api.multi
    def action_cancel(self):
        for record in self:
            purchase_order_objects = self.env['purchase.order'].sudo().search(
                ['|', ('sale_order_id', '=', record.id), ('origin', '=', record.name)])
            for purchase_order in purchase_order_objects:
                if purchase_order.state not in ('done', 'cancel', 'purchase'):
                    purchase_order.button_cancel()
                else:
                    raise ValidationError(
                        _("You have already proceed in purchase order (%s)") % (purchase_order.name))

            purchase_order_line_objects = self.env['purchase.order.line'].sudo().search(
                [('sale_order_id', '=', record.id)])
            for purchase_order_line in purchase_order_line_objects:
                if purchase_order_line.order_id not in purchase_order_line_objects:
                    if purchase_order_line.order_id.state not in ['done', 'cancel', 'purchase']:
                        purchase_order_line.unlink()
                    else:
                        raise ValidationError(
                            _("You have already proceed in purchase order (%s)") % (purchase_order_line.order_id.name))

            # related manufacturing order
            mos = self.env['mrp.production'].sudo().search(
                [('sale_order_id', '=', record.id), ('state', '!=', 'cancel')])

            for production_order in self.env['production.sale.order'].sudo().search(
                    [('sale_order_id', '=', record.id), ('status', '!=', 'cancel')]):
                if production_order.production_id not in mos and production_order.production_id.state != 'cancel':
                    mos += production_order.production_id

            for mo in mos:
                if mo.state not in ['confirmed', 'cancel']:
                    raise ValidationError(_("You have already proceed in manufacturing order (%s)") % (mo.name))

                total_qty = 0

                for production_order in self.env['production.sale.order'].sudo().search(
                        [('production_id', '=', mo.id), ('sale_order_id', '=', record.id), ('status', '!=', 'cancel')]):
                    total_qty += production_order.qty_to_produce
                    production_order.write({'status': 'cancel'})
                if mo.product_qty <= total_qty:
                    mo.action_cancel()
                else:
                    mo.change_product_qty(-total_qty)
        return super(SaleOrder, self).action_cancel()
