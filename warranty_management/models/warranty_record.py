from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class WarrantyRecord(models.Model):
    _name = 'warranty.record'
    _description = 'Warranty Record'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'end_date desc, id desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    sale_line_id = fields.Many2one('sale.order.line', required=True, ondelete='cascade')
    sale_order_id = fields.Many2one(
        'sale.order', related='sale_line_id.order_id', store=True, string='Sale Order')
    partner_id = fields.Many2one('res.partner', required=True, tracking=True)
    product_id = fields.Many2one('product.product', required=True)
    quantity = fields.Float(default=1.0)
    lot_id = fields.Many2one('stock.lot', string='Serial / Lot')

    start_date = fields.Date(required=True, tracking=True)
    duration_months = fields.Integer(required=True)
    extra_months = fields.Integer(string='Extended Months', default=0)
    end_date = fields.Date(compute='_compute_end_date', store=True, tracking=True)
    days_left = fields.Integer(compute='_compute_days_left')

    state = fields.Selection([
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], default='active', tracking=True)

    claim_ids = fields.One2many('warranty.claim', 'warranty_id')
    claim_count = fields.Integer(compute='_compute_claim_count')
    company_id = fields.Many2one(
        'res.company', related='sale_order_id.company_id', store=True)

    @api.depends('start_date', 'duration_months', 'extra_months')
    def _compute_end_date(self):
        for rec in self:
            if rec.start_date:
                rec.end_date = rec.start_date + relativedelta(
                    months=rec.duration_months + rec.extra_months)
            else:
                rec.end_date = False

    @api.depends('end_date', 'state')
    def _compute_days_left(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.state == 'active' and rec.end_date:
                rec.days_left = max((rec.end_date - today).days, 0)
            else:
                rec.days_left = 0

    def _compute_claim_count(self):
        for rec in self:
            rec.claim_count = len(rec.claim_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('warranty.record') or 'New'
        return super().create(vals_list)

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = f'/my/warranties/{rec.id}'

    def is_valid_on(self, date):
        self.ensure_one()
        return self.state == 'active' and self.start_date <= date <= self.end_date

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_view_claims(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Claims',
            'res_model': 'warranty.claim',
            'view_mode': 'list,form',
            'domain': [('warranty_id', '=', self.id)],
            'context': {'default_warranty_id': self.id},
        }

    # ---------- Cron ----------
    @api.model
    def _cron_update_states(self):
        today = fields.Date.context_today(self)
        expired = self.search([('state', '=', 'active'), ('end_date', '<', today)])
        expired.write({'state': 'expired'})

    @api.model
    def _cron_notify_expiring(self, days=30):
        target = fields.Date.context_today(self) + relativedelta(days=days)
        records = self.search([('state', '=', 'active'), ('end_date', '=', target)])
        template = self.env.ref(
            'warranty_management.mail_template_warranty_expiring', raise_if_not_found=False)
        if template:
            for rec in records:
                template.send_mail(rec.id, force_send=False)