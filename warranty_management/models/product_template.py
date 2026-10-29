from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warranty_months = fields.Integer(
        string='Warranty Duration (Months)',
        default=0,
        help='0 means this product has no warranty.',
    )