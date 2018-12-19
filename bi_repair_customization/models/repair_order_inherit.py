# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    receive_date = fields.Date(string="Received Date")
    finish_date = fields.Date(string="Finished Date")
    location = fields.Char(string="Location")

    @api.constrains('receive_date','finish_date')
    def check_repair_order_dates(self):
        for order in self:
            if order.finish_date and order.receive_date:
                if order.receive_date > order.finish_date:
                    raise ValidationError(_('Order received date must be less than order finished date.'))


