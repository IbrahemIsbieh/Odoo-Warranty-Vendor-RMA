from odoo import _, fields, models


class WarrantyExtension(models.Model):
    _name = 'warranty.extension'
    _description = 'Warranty Extension'
    _order = 'date desc, id desc'

    warranty_id = fields.Many2one(
        'warranty.record', required=True, ondelete='cascade', index=True)
    plan_id = fields.Many2one('warranty.extension.plan', ondelete='restrict')
    months = fields.Integer(required=True)
    date = fields.Date(default=fields.Date.context_today)
    sale_line_id = fields.Many2one('sale.order.line', ondelete='set null')
    currency_id = fields.Many2one('res.currency', required=True)
    amount = fields.Monetary(currency_field='currency_id')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    state = fields.Selection([
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
    ], default='active', required=True)
    cancel_reason = fields.Char(readonly=True)

    def _sync_state(self, force_cancel=False):
        """Align the extension state with its sale order line."""
        for ext in self:
            line = ext.sale_line_id
            reason = False
            if force_cancel or not line:
                new_state, reason = 'cancelled', _('order line removed')
            elif line.order_id.state == 'cancel':
                new_state, reason = 'cancelled', _('order cancelled')
            elif line.product_uom_qty <= 0:
                new_state, reason = 'cancelled', _('order line quantity set to zero')
            else:
                new_state = 'active'

            if new_state == ext.state:
                continue

            ext.write({'state': new_state, 'cancel_reason': reason})
            warranty = ext.warranty_id
            if new_state == 'cancelled':
                body = _(
                    'Extension of %(months)s months cancelled (%(reason)s). New end date: %(end)s.',
                    months=ext.months, reason=reason, end=warranty.end_date)
            else:
                body = _(
                    'Extension of %(months)s months restored. New end date: %(end)s.',
                    months=ext.months, end=warranty.end_date)
            warranty.message_post(body=body)