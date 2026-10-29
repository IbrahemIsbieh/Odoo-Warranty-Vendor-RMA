from odoo import fields, models


class ClaimResolveWizard(models.TransientModel):
    _name = 'warranty.claim.resolve.wizard'
    _description = 'Resolve Warranty Claim'

    claim_id = fields.Many2one('warranty.claim', required=True)
    resolution = fields.Selection([
        ('repair', 'Repair'),
        ('replace', 'Replacement'),
        ('refund', 'Refund'),
    ], required=True, default='repair')
    note = fields.Text()

    def action_confirm(self):
        self.ensure_one()
        claim = self.claim_id
        claim.write({
            'resolution': self.resolution,
            'resolution_note': self.note,
            'state': 'repair' if self.resolution == 'repair' else 'closed',
        })
        claim.message_post(
            body=f'Resolution: {dict(self._fields["resolution"].selection)[self.resolution]}')
        return {'type': 'ir.actions.act_window_close'}