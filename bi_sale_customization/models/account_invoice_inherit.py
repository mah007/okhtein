# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    po_number = fields.Char(string="PO Number")
    shipment_number = fields.Char(string="Shipment Number")
    print_hs_code = fields.Boolean(string="Print HS Code")


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    hs_code = fields.Char(string="HS Code", store=True, related='product_id.hs_code', readonly=True)
    color = fields.Char(string="Color", store=True, related='product_id.color', readonly=True)
    image = fields.Binary(
        "image", related='product_id.image_small', readonly=True)
