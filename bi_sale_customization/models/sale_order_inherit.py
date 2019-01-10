# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    po_number = fields.Char(string="PO Number")
    shipment_number = fields.Char(string="Shipment Number")
    print_hs_code = fields.Boolean(string="Print HS Code")
    expected_date = fields.Datetime("Expected Date", compute=False, readonly=False, store=True,
                                    oldname='commitment_date',
                                    help="Delivery date you can promise to the customer, computed from product lead times and from the shipping policy of the order.")

    @api.multi
    @api.onchange('order_line.customer_lead', 'confirmation_date', 'order_line')
    def change_expected_date(self):
        for order in self:
            dates_list = []
            confirm_date = fields.Datetime.from_string(
                (order.confirmation_date or order.write_date) if order.state == 'sale' else fields.Datetime.now())
            for line in order.order_line.filtered(lambda x: x.state != 'cancel' and not x._is_delivery()):
                dt = confirm_date + timedelta(days=line.customer_lead or 0.0)
                dates_list.append(dt)
            if dates_list:
                order.expected_date = fields.Datetime.to_string(min(dates_list))

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['po_number'] = self.po_number or False
        invoice_vals['shipment_number'] = self.shipment_number or False
        invoice_vals['print_hs_code'] = self.print_hs_code or False
        return invoice_vals

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.expected_date and order.picking_ids:
                for picking in order.picking_ids:
                    picking.write({'scheduled_date': order.expected_date})
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hs_code = fields.Char(string="HS Code", store=True, related='product_id.hs_code', readonly=True)
    color = fields.Char(string="Color", store=True, related='product_id.color', readonly=True)
    image = fields.Binary(
        "image", related='product_id.image_small', readonly=True)
