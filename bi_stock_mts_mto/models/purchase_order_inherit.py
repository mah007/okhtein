# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order",readonly=False)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order",readonly=False)
