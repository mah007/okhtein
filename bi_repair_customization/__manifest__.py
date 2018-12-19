# -*- coding: utf-8 -*-
{
    'name': "BI Repair Customization",
    'summary': "BI Repair Customization",
    'description': """ 
            This module adds new fields to repair module.
     """,
    'author': "BI Solutions Development Team",
    'category': 'Accounting',
    'version': '0.1',
    'depends': ['base','repair'],
    'data': [
        'views/repair_order_inherit_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'sequence': 1
}
