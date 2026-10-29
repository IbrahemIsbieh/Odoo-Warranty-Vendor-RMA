from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    extension_ids = fields.One2many('warranty.extension', 'sale_line_id')

    def write(self, vals):
        res = super().write(vals)
        if 'product_uom_qty' in vals:
            self.sudo().extension_ids._sync_state()
        return res

    def unlink(self):
        # must run before the delete, afterwards the link is already nulled
        self.sudo().extension_ids._sync_state(force_cancel=True)
        return super().unlink()