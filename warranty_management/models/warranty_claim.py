from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class WarrantyClaim(models.Model):
    _name = 'warranty.claim'
    _description = 'Warranty Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    warranty_id = fields.Many2one(
        'warranty.record', required=True, tracking=True, ondelete='restrict')
    partner_id = fields.Many2one(
        'res.partner', related='warranty_id.partner_id', store=True)
    product_id = fields.Many2one(
        'product.product', related='warranty_id.product_id', store=True)
    claim_date = fields.Date(default=fields.Date.context_today, required=True)
    description = fields.Text(string='Issue Description', required=True)
    is_in_warranty = fields.Boolean(compute='_compute_is_in_warranty', store=True)

    state = fields.Selection([
        ('new', 'New'),
        ('review', 'Under Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('repair', 'In Repair'),
        ('closed', 'Closed'),
    ], default='new', tracking=True, group_expand='_group_expand_states')

    reject_reason = fields.Text(readonly=True, tracking=True)
    resolution = fields.Selection([
        ('repair', 'Repair'),
        ('replace', 'Replacement'),
        ('refund', 'Refund'),
    ], readonly=True, tracking=True)
    resolution_note = fields.Text(readonly=True)
    user_id = fields.Many2one(
        'res.users', string='Assigned To', default=lambda self: self.env.user, tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Photos / Files')

    @api.model
    def _group_expand_states(self, states, domain):
        return [key for key, _label in self._fields['state'].selection]

    @api.depends('warranty_id.state', 'warranty_id.start_date',
                 'warranty_id.end_date', 'claim_date')
    def _compute_is_in_warranty(self):
        for rec in self:
            rec.is_in_warranty = bool(
                rec.warranty_id and rec.claim_date and rec.warranty_id.is_valid_on(rec.claim_date))

    @api.constrains('warranty_id', 'claim_date')
    def _check_warranty_valid(self):
        for rec in self:
            if rec.state == 'new' and not rec.is_in_warranty:
                raise ValidationError(
                    _('This warranty is not valid on the claim date, the claim cannot be created.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('warranty.claim') or 'New'
        return super().create(vals_list)

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = f'/my/warranty-claims/{rec.id}'

    # ---------- Workflow ----------
    def action_review(self):
        self.write({'state': 'review'})

    def action_accept(self):
        self.write({'state': 'accepted'})

    def action_start_repair(self):
        for rec in self:
            if rec.state != 'accepted':
                raise UserError(_('Only accepted claims can go to repair.'))
        self.write({'state': 'repair'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_open_reject_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Claim',
            'res_model': 'warranty.claim.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_claim_id': self.id},
        }

    def action_open_resolve_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resolve Claim',
            'res_model': 'warranty.claim.resolve.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_claim_id': self.id},
        }