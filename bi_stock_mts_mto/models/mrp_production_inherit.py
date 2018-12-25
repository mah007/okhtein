# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one('sale.order', string="Source Document")
    sale_production_ids = fields.One2many('production.sale.order', 'sale_order_id', string="Sale Orders")
    customer_reference = fields.Char(string='Customer', copy=False, readonly=True)
    product_qty = fields.Float(string='Quantity To Produce', default=1.0, readonly=True, required=True,
                               track_visibility='onchange', states={'confirmed': [('readonly', False)]})
