# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductionSaleOrder(models.Model):
    _name = 'production.sale.order'
    _rec_name = 'production_id'

    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', )
    customer_id = fields.Many2one("res.partner", related='sale_order_id.partner_id', string='Customer', readonly=True)
    project_name = fields.Char(related='sale_order_id.project_name', string='Project', readonly=True)
    customer_po = fields.Char(related='sale_order_id.customer_po', string='Customer PO', readonly=True)
    ordered_qty = fields.Float('Ordered Qty', readonly=True)
    avail_qty = fields.Float('Available Qty', readonly=True)
    qty_to_produce = fields.Float('Manufactured Qty', readonly=True)
    status = fields.Selection([('sale', 'Sales Order'), ('locked', 'Locked'), ('cancel', 'Cancelled')], string='Status',
                              readonly=True)
