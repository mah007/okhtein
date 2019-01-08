# -*- coding: utf-8 -*-
{
    'name': "BI Sale Customization",
    'summary': "BI Sale Customization",
    'description': """ 
            This module adds new features to sale module.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Sale',
    'version': '0.1',
    'depends': ['sale', 'hr', 'purchase', 'stock', 'delivery_hs_code'],
    'data': [
        'views/sale_order_inherit_view.xml',
        'views/purchase_order_inherit_view.xml',
        'views/account_invoice_inherit_view.xml',
        'views/product_template_inherit_view.xml',
        'views/stock_picking_inherit_view.xml',
        'reports/sale_order_report_inherit.xml',
        'reports/invoice_report_inherit.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
