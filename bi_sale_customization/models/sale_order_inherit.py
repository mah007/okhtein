# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    po_num = fields.Char(string="PO Number")
    ship_num = fields.Char(string="Shipment Number")
    hs_is_active = fields.Boolean(string="Print HS Code")


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template',
                                      related='product_id.product_tmpl_id', readonly=True)
    hs_code = fields.Char(string="HS Code", store=True, related='product_id.product_tmpl_id.hs_code', readonly=True)
    color = fields.Char(string="Color", store=True, related='product_id.product_tmpl_id.color', readonly=True)
    image = fields.Binary(
        "image", related='product_id.product_tmpl_id.image_small', readonly=True)
