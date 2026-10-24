# -*- coding: utf-8 -*-
{
    'name': 'Store Operation Requests',
    'version': '19.0.1.7.0',
    'category': 'Purchases',
    'summary': 'Manage material requisition of employees and user',
    'description': """Create the material requisition request and there are
    multi-level approvals for requests from the department head and requisition
    manager. Department head has the option to choose vendors for each material.
    Also we can generate the PDF report for each material requisition""",
    'author': 'OdoCore',
    'company': 'OdoCore',
    'maintainer': 'OdoCore',
    'website': 'https://www.odocore.com',
    'depends': ['mail', 'hr', 'stock', 'purchase', 'purchase_stock'],
    'data': [
        'security/employee_purchase_requisition_groups.xml',
        'security/employee_purchase_requisition_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/dashboard_views.xml',
        'views/employee_purchase_requisition_views.xml',
        'views/requisition_order_views.xml',
        'views/return_request_views.xml',
        'views/return_request_line_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_department_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/res_users_views.xml',
        'views/employee_purchase_requisition_menu.xml',
        'report/employee_purchase_requisition_templates.xml',
        'report/employee_purchase_requisition_report.xml',
        'report/return_request_templates.xml',
        'report/return_request_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'store_operation_requests/static/src/js/**/*',
            'store_operation_requests/static/src/xml/**/*',
            'store_operation_requests/static/src/scss/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
