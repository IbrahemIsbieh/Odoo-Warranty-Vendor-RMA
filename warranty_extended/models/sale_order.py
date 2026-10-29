from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            # cancel, back to quotation, confirm: re-evaluate extensions
            self.sudo().order_line.extension_ids._sync_state()
        return res