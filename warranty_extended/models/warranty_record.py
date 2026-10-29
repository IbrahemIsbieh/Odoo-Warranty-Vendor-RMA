from odoo import api, fields, models


class WarrantyRecord(models.Model):
    _inherit = 'warranty.record'

    extension_ids = fields.One2many('warranty.extension', 'warranty_id', string='Extensions')
    extra_months = fields.Integer(
        string='Extended Months', compute='_compute_extra_months', store=True)

    @api.depends('extension_ids.months', 'extension_ids.state')
    def _compute_extra_months(self):
        for rec in self:
            rec.extra_months = sum(
                rec.extension_ids.filtered(lambda e: e.state == 'active').mapped('months'))

    def action_open_extend_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Extend Warranty',
            'res_model': 'warranty.extend.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_warranty_id': self.id},
        }