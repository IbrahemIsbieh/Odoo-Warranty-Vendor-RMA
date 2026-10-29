from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vendor_warranty_months = fields.Integer(
        string='Vendor Warranty (Months)',
        help='Warranty duration granted by the vendor, counted from the receipt date.')