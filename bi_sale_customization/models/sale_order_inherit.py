# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    po_number = fields.Char(string="PO Number")
    shipment_number = fields.Char(string="Shipment Number")
    print_hs_code = fields.Boolean(string="Print HS Code")

    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['po_number'] = self.po_number or False
        invoice_vals['shipment_number'] = self.shipment_number or False
        invoice_vals['print_hs_code'] = self.print_hs_code or False
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    hs_code = fields.Char(string="HS Code", store=True, related='product_id.hs_code', readonly=True)
    color = fields.Char(string="Color", store=True, related='product_id.color', readonly=True)
    image = fields.Binary(
        "image", related='product_id.image_small', readonly=True)
