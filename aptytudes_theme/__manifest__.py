# -*- coding: utf-8 -*-
{
    'name': 'Aptytudes Theme',
    'version': '18.0.1.0.0',
    'website': 'https://www.applylog.com',
    'category': 'Theme/Backend',
    'sequence': 1,
    'summary': 'Personnalisation visuelle du backend Odoo',
    'description': """
Thème backend custom pour OSETEAM.
""",
    'author': 'Applylog',
    'maintainer': 'Applylog',
    'license': 'LGPL-3',
    'depends': ['web', 'account'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'aptytudes_theme/static/src/css/form_inputs.css',
            'aptytudes_theme/static/src/css/list_view.css',
            'aptytudes_theme/static/src/js/required_field_empty.js',
            'aptytudes_theme/static/src/js/order_line_description_focus.js',
            'aptytudes_theme/static/src/js/order_line_description_autoshow.js',
            'aptytudes_theme/static/src/js/list_column_widths_memory.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
