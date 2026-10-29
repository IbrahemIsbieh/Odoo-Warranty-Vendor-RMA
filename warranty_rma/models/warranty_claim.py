from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WarrantyClaim(models.Model):
    _inherit = 'warranty.claim'

    rma_ids = fields.One2many('warranty.rma', 'claim_id', string='Vendor RMAs')
    rma_count = fields.Integer(compute='_compute_rma_count')

    @api.depends('rma_ids')
    def _compute_rma_count(self):
        for claim in self:
            claim.rma_count = len(claim.rma_ids)

    def action_create_rma(self):
        self.ensure_one()
        if self.state not in ('accepted', 'repair', 'closed'):
            raise UserError(_('Accept the claim before opening a vendor RMA.'))
        rma = self.rma_ids.filtered(lambda r: r.state != 'cancelled')[:1]
        if not rma:
            rma = self.env['warranty.rma'].create({
                'claim_id': self.id,
                'lot_id': self.warranty_id.lot_id.id,
            })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'warranty.rma',
            'res_id': rma.id,
            'view_mode': 'form',
        }

    def action_view_rmas(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor RMAs',
            'res_model': 'warranty.rma',
            'view_mode': 'list,form',
            'domain': [('claim_id', '=', self.id)],
        }