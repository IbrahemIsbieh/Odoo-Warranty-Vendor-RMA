from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WarrantyExtendWizard(models.TransientModel):
    _name = 'warranty.extend.wizard'
    _description = 'Extend Warranty Wizard'

    warranty_id = fields.Many2one('warranty.record', required=True)
    plan_id = fields.Many2one('warranty.extension.plan', required=True)
    currency_id = fields.Many2one(
        'res.currency', related='warranty_id.sale_order_id.currency_id')
    base_amount = fields.Monetary(
        compute='_compute_amounts', currency_field='currency_id',
        string='Product Price')
    amount = fields.Monetary(
        compute='_compute_amounts', currency_field='currency_id',
        string='Extension Price')
    current_end_date = fields.Date(related='warranty_id.end_date')
    new_end_date = fields.Date(compute='_compute_new_end_date')

    @api.depends('warranty_id.sale_line_id.price_subtotal', 'plan_id.percent')
    def _compute_amounts(self):
        for wiz in self:
            base = wiz.warranty_id.sale_line_id.price_subtotal
            wiz.base_amount = base
            wiz.amount = base * wiz.plan_id.percent / 100.0

    @api.depends('warranty_id.start_date', 'warranty_id.duration_months',
                 'warranty_id.extra_months', 'plan_id.months')
    def _compute_new_end_date(self):
        for wiz in self:
            w = wiz.warranty_id
            if w.start_date and wiz.plan_id:
                wiz.new_end_date = w.start_date + relativedelta(
                    months=w.duration_months + w.extra_months + wiz.plan_id.months)
            else:
                wiz.new_end_date = False

    def action_confirm(self):
        self.ensure_one()
        warranty = self.warranty_id
        plan = self.plan_id
        order = warranty.sale_order_id

        if warranty.state != 'active':
            raise UserError(_('Only active warranties can be extended.'))
        if order.state not in ('draft', 'sent', 'sale') or order.locked:
            raise UserError(_(
                'The sale order %s is locked or cancelled, unlock it first to add the extension.',
                order.name))

        product = self.env.ref('warranty_extended.product_extended_warranty').product_variant_id
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': product.id,
            'name': _('Extended Warranty (%(plan)s) - %(product)s [%(ref)s]',
                      plan=plan.name,
                      product=warranty.product_id.display_name,
                      ref=warranty.name),
            'product_uom_qty': 1,
            'price_unit': self.amount,
        })
        # extra_months on the warranty is computed from the active extensions,
        # so creating the extension is enough to push the end date forward.
        self.env['warranty.extension'].create({
            'warranty_id': warranty.id,
            'plan_id': plan.id,
            'months': plan.months,
            'sale_line_id': line.id,
            'currency_id': order.currency_id.id,
            'amount': self.amount,
        })
        warranty.message_post(body=_(
            'Warranty extended by %(months)s months (%(plan)s). New end date: %(end)s.',
            months=plan.months, plan=plan.name, end=warranty.end_date))
        return {'type': 'ir.actions.act_window_close'}