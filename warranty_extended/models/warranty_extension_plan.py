from odoo import fields, models


class WarrantyExtensionPlan(models.Model):
    _name = 'warranty.extension.plan'
    _description = 'Warranty Extension Plan'
    _order = 'months'

    name = fields.Char(required=True, translate=True)
    months = fields.Integer(required=True)
    percent = fields.Float(
        string='Price (% of product price)', required=True,
        help='Extension price as a percentage of the original order line subtotal.')
    active = fields.Boolean(default=True)

    _check_months = models.Constraint(
        'CHECK(months > 0)', 'Months must be greater than zero.')
    _check_percent = models.Constraint(
        'CHECK(percent >= 0)', 'Percentage cannot be negative.')