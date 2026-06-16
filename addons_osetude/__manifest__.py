# -*- coding: utf-8 -*-
{
    'name': 'Tools for OSETEAM',
    'version': '18.0.1.0.0',  # Format recommandé : odoo_series.addon_major.addon_minor.addon_patch.addon_build
    'website': 'https://www.applylog.com',
    'category': 'Project/Tools',
    'sequence': 10,
    'summary': 'Custom tools for OSETEAM projects and management',
    'description': """
Custom tools for OSETEAM projects and management
""",
    'author': 'Applylog',
    'maintainer': 'Applylog',
    'license': 'LGPL-3',
    'support': 'support@applylog.com',  # Ajout pour indiquer le support
    'depends': [
        'base',
        'project',
        'sale_management',
        'stock',
        'sale_stock',
        'account',
        'sale_timesheet',
        'sale_margin',
        'hr_timesheet',
        #'hr_holidays',VOIR SI NECESSAIRE
        'hr_expense',
        'purchase',
        'contacts',
        'base_import',
        'web',  # Ajout recommandé pour les modules utilisant des assets web
    ],
    'data': [
        # Sécurité et données
        'datas/ir_module_category_data.xml',
        'security/osetude_security.xml',
        'security/ir.model.access.csv',
        'datas/system_parameter.xml',
        'datas/quality_control_checklist_data.xml',
        'datas/ir_sequence_data.xml',

        # Rapports
        #'report/external_layout_standard.xml',
        'report/report_paper_format.xml',
        'report/project_report.xml',
        'report/project_report_templates.xml',
        #'report/sale_report_templates.xml',
        #'report/invoice_report_template.xml',
        #'report/purchase_report_templates.xml',
        'report/report_deliveryslip.xml',

        # Vues
        'views/project_view.xml',
        'views/sale_view.xml',
        'views/purchase_view.xml',
        'views/account_move_view.xml',
        'views/stock_picking_view.xml',
        'views/hr_timesheet_view.xml',
        'views/res_partner_view.xml',
        'views/quality_control_quality_view.xml',
        'views/hr_expense_views.xml',
        'views/account_view.xml',
        'views/hr_leave_view.xml',
        'views/satisfaction_survey_view.xml',

        # Assistants
        'wizard/create_purchase_order_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            ('prepend', 'addons_osetude/static/src/css/style.css'),  # Utilisation de tuple pour spécifier l'ordre
            ('prepend', 'addons_osetude/static/src/css/style_analyse.css'),
        ],
        'web.assets_qweb': [
            'addons_osetude/static/src/xml/*.xml',  # Décommentez si vous avez des templates QWeb
        ],
    },
    'demo': [
        # 'demo/demo_data.xml',  # Ajoutez ici vos fichiers de démonstration si nécessaire
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

