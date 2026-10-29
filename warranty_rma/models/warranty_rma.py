from dateutil.relativedelta import relativedelta

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class WarrantyRma(models.Model):
    _name = 'warranty.rma'
    _description = 'Vendor RMA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    claim_id = fields.Many2one(
        'warranty.claim', required=True, ondelete='restrict', tracking=True)
    warranty_id = fields.Many2one(
        'warranty.record', related='claim_id.warranty_id', store=True)
    product_id = fields.Many2one(
        'product.product', related='claim_id.product_id', store=True)
    customer_id = fields.Many2one(
        'res.partner', related='claim_id.partner_id', store=True, string='Customer')
    lot_id = fields.Many2one(
        'stock.lot', string='Serial / Lot', tracking=True,
        domain="[('product_id', '=', product_id)]")

    # Vendor info: auto-filled from the lot, but editable for untracked products
    vendor_id = fields.Many2one(
        'res.partner', string='Vendor', compute='_compute_vendor_info',
        store=True, readonly=False, tracking=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order', compute='_compute_vendor_info',
        store=True, readonly=False)
    receipt_date = fields.Date(
        string='Received On', compute='_compute_vendor_info',
        store=True, readonly=False)
    vendor_warranty_end = fields.Date(
        compute='_compute_vendor_warranty_end', store=True)
    is_vendor_covered = fields.Boolean(compute='_compute_is_vendor_covered')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to Vendor'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    resolution = fields.Selection([
        ('replacement', 'Replacement'),
        ('repair', 'Repair'),
        ('credit', 'Credit Note'),
        ('rejected', 'Rejected by Vendor'),
    ], tracking=True)
    note = fields.Text()
    return_picking_id = fields.Many2one('stock.picking', readonly=True, copy=False)
    replacement_picking_id = fields.Many2one('stock.picking', readonly=True, copy=False)
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company)

    # ---------- Computes ----------
    @api.depends('lot_id')
    def _compute_vendor_info(self):
        MoveLine = self.env['stock.move.line'].sudo()
        for rma in self:
            vendor, po, date = rma.vendor_id, rma.purchase_order_id, rma.receipt_date
            if rma.lot_id:
                ml = MoveLine.search([
                    ('lot_id', '=', rma.lot_id.id),
                    ('state', '=', 'done'),
                    ('picking_id.picking_type_id.code', '=', 'incoming'),
                ], order='date desc, id desc', limit=1)
                if ml:
                    po = ml.move_id.purchase_line_id.order_id
                    vendor = po.partner_id or ml.picking_id.partner_id
                    date = ml.date.date() if ml.date else False
            rma.vendor_id = vendor
            rma.purchase_order_id = po
            rma.receipt_date = date

    @api.depends('receipt_date', 'product_id.product_tmpl_id.vendor_warranty_months')
    def _compute_vendor_warranty_end(self):
        for rma in self:
            months = rma.product_id.product_tmpl_id.vendor_warranty_months
            if rma.receipt_date and months:
                rma.vendor_warranty_end = rma.receipt_date + relativedelta(months=months)
            else:
                rma.vendor_warranty_end = False

    @api.depends('vendor_warranty_end')
    def _compute_is_vendor_covered(self):
        today = fields.Date.context_today(self)
        for rma in self:
            rma.is_vendor_covered = bool(
                rma.vendor_warranty_end and today <= rma.vendor_warranty_end)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('warranty.rma') or 'New'
        return super().create(vals_list)

    # ---------- Stock helpers ----------
    def _get_warehouse(self):
        self.ensure_one()
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.company_id.id)], limit=1)
        if not warehouse:
            raise UserError(_('No warehouse found for company %s.', self.company_id.name))
        return warehouse

    def _prepare_move_vals(self, src, dest):
        self.ensure_one()
        vals = {
            'product_id': self.product_id.id,
            'product_uom_qty': 1.0,
            'product_uom': self.product_id.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
        }
        if 'name' in self.env['stock.move']._fields:
            vals['name'] = self.name
        return vals

    def _create_return_picking(self):
        self.ensure_one()
        warehouse = self._get_warehouse()
        src = warehouse.lot_stock_id
        dest = (self.vendor_id.property_stock_supplier
                or self.env.ref('stock.stock_location_suppliers'))
        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': warehouse.out_type_id.id,
            'partner_id': self.vendor_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'origin': self.name,
            'move_ids': [Command.create(self._prepare_move_vals(src, dest))],
        })
        picking.action_confirm()
        if self.lot_id:
            move = picking.move_ids
            self.env['stock.move.line'].sudo().create({
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': self.product_id.id,
                'product_uom_id': move.product_uom.id,
                'lot_id': self.lot_id.id,
                'quantity': 1.0,
                'location_id': src.id,
                'location_dest_id': dest.id,
            })
        else:
            picking.action_assign()
        return picking

    def _create_replacement_picking(self):
        self.ensure_one()
        warehouse = self._get_warehouse()
        src = (self.vendor_id.property_stock_supplier
               or self.env.ref('stock.stock_location_suppliers'))
        dest = warehouse.lot_stock_id
        picking = self.env['stock.picking'].sudo().create({
            'picking_type_id': warehouse.in_type_id.id,
            'partner_id': self.vendor_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'origin': self.name,
            'move_ids': [Command.create(self._prepare_move_vals(src, dest))],
        })
        picking.action_confirm()
        return picking

    # ---------- Workflow ----------
    def action_send(self):
        for rma in self:
            if rma.state != 'draft':
                raise UserError(_('Only draft RMAs can be sent to the vendor.'))
            if not rma.vendor_id:
                raise UserError(_('Please set the vendor first.'))
            picking = rma._create_return_picking()
            rma.write({'return_picking_id': picking.id, 'state': 'sent'})
            rma.message_post(body=_('Return to vendor created: %s.', picking.name))

    def action_resolve(self):
        for rma in self:
            if rma.state != 'sent':
                raise UserError(_('Only RMAs sent to the vendor can be resolved.'))
            if not rma.resolution:
                raise UserError(_('Select the vendor resolution first.'))
            if rma.resolution == 'replacement' and not rma.replacement_picking_id:
                picking = rma._create_replacement_picking()
                rma.replacement_picking_id = picking.id
                rma.message_post(body=_('Expected replacement receipt: %s.', picking.name))
            rma.state = 'resolved'

    def action_cancel(self):
        for rma in self:
            pickings = rma.return_picking_id | rma.replacement_picking_id
            if any(p.state == 'done' for p in pickings):
                raise UserError(_('A related transfer is already done, this RMA cannot be cancelled.'))
            pickings.filtered(lambda p: p.state != 'cancel').sudo().action_cancel()
            rma.state = 'cancelled'

    def _open_picking(self, picking):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
        }

    def action_view_return_picking(self):
        return self._open_picking(self.return_picking_id)

    def action_view_replacement_picking(self):
        return self._open_picking(self.replacement_picking_id)