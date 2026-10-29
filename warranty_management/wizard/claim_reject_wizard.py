from odoo import fields, models


class ClaimRejectWizard(models.TransientModel):
    _name = 'warranty.claim.reject.wizard'
    _description = 'Reject Warranty Claim'

    claim_id = fields.Many2one('warranty.claim', required=True)
    reason = fields.Text(required=True)

    def action_confirm(self):
        self.ensure_one()
        self.claim_id.write({'state': 'rejected', 'reject_reason': self.reason})
        self.claim_id.message_post(body=f'Claim rejected. Reason: {self.reason}')
        return {'type': 'ir.actions.act_window_close'}