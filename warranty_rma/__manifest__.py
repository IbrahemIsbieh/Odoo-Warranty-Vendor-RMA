{
    'name': 'Warranty RMA',
    'version': '19.0.1.0.0',
    'summary': 'Vendor warranty tracking and RMA with stock returns',
    'category': 'Inventory',
    'author': 'Ibrahem Issa',
    'depends': ['warranty_management', 'purchase_stock', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/product_views.xml',
        'views/warranty_rma_views.xml',
        'views/warranty_claim_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}