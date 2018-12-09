# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template',
                                      related='product_id.product_tmpl_id', readonly=True)
    hs_code = fields.Char(string="HS Code", store=True, related='product_id.product_tmpl_id.hs_code', readonly=True)
    color = fields.Char(string="Color", store=True, related='product_id.product_tmpl_id.color', readonly=True)
    image = fields.Binary(
        "image", related='product_id.product_tmpl_id.image_small', readonly=True)
