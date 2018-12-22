# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"

    is_mts = fields.Boolean(string='Is Mts ??')
