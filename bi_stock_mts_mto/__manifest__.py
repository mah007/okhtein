# -*- coding: utf-8 -*-
{
    'name': 'BI Stock MTS - MTO',
    'summary': 'BI Stock MTS - MTO',
    'description': """

     """,
    'author': "BI Solutions Development Team",
    'category': 'Manufacturing',
    'version': '0.1',
    'depends': ['account', 'sale_management', 'purchase', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_location_route_data.xml',
        'views/production_sale_order_view.xml',
        'views/sale_order_inherit_view.xml',
        'views/mrp_production_inherit_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
