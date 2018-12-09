# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    color = fields.Char(string="Color", store=True)


class ProductProduct(models.Model):
    _inherit = "product.product"

    color = fields.Char(string="Color", store=True)
