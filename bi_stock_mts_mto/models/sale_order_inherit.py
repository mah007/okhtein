# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    project_name = fields.Char(string='Project')
    customer_po = fields.Char(string='Customer PO')
