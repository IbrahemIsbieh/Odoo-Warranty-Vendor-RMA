from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        res = super()._action_done()
        Warranty = self.env['warranty.record'].sudo()
        for picking in self.filtered(lambda p: p.picking_type_code == 'outgoing'):
            for move in picking.move_ids:
                if not move.sale_line_id:
                    continue
                lots = move.move_line_ids.lot_id
                if len(lots) != 1:
                    continue
                warranty = Warranty.search([
                    ('sale_line_id', '=', move.sale_line_id.id),
                    ('lot_id', '=', False),
                ], limit=1)
                if warranty:
                    warranty.lot_id = lots
        return res