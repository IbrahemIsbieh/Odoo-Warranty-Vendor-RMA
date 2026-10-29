from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    warranty_ids = fields.One2many('warranty.record', 'sale_order_id', string='Warranties')
    warranty_count = fields.Integer(compute='_compute_warranty_count')

    def _compute_warranty_count(self):
        for order in self:
            order.warranty_count = len(order.warranty_ids)

    def _action_confirm(self):
        res = super()._action_confirm()
        for order in self:
            order._create_warranty_records()
        return res

    def _create_warranty_records(self):
        self.ensure_one()
        Warranty = self.env['warranty.record']
        for line in self.order_line:
            product = line.product_id
            if line.display_type or not product or product.type == 'service':
                continue
            months = product.product_tmpl_id.warranty_months
            if months <= 0:
                continue
            # skip if already generated for this line (re-confirm after cancel)
            if Warranty.search_count([('sale_line_id', '=', line.id)]):
                continue
            Warranty.create({
                'sale_line_id': line.id,
                'partner_id': self.partner_id.id,
                'product_id': product.id,
                'quantity': line.product_uom_qty,
                'start_date': fields.Date.context_today(self),
                'duration_months': months,
            })

    def action_view_warranties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Warranties',
            'res_model': 'warranty.record',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
        }