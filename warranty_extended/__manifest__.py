{
    'name': 'Warranty Extended',
    'version': '19.0.1.0.0',
    'summary': 'Sell extended warranty plans on top of existing warranties',
    'category': 'Sales',
    'author': 'Ibrahem Issa',
    'depends': ['warranty_management', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/extended_data.xml',
        'views/warranty_extension_plan_views.xml',
        'wizard/warranty_extend_wizard_views.xml',
        'views/warranty_record_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}