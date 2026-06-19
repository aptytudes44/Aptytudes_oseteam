{
    'name': 'Stock Picking Signature',
    'version': '1.0',
    'summary': 'Add online signature to delivery orders',
    'description': 'Allows customers to sign delivery orders online, like quotations.',
    'author': 'APPLYLOG',
    'depends': ['base', 'stock', 'web', 'mail', 'portal'],
    'data': [
        'data/mail_template_data.xml',
        'views/stock_picking_views.xml',
        'views/templates.xml',
        'views/report_picking.xml',
    ],
    'installable': True,
    'application': False,
}
