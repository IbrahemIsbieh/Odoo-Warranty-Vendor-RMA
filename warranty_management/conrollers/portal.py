from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class WarrantyPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id.commercial_partner_id
        if 'warranty_count' in counters:
            values['warranty_count'] = request.env['warranty.record'].search_count(
                [('partner_id', 'child_of', partner.id)])
        if 'claim_count' in counters:
            values['claim_count'] = request.env['warranty.claim'].search_count(
                [('partner_id', 'child_of', partner.id)])
        return values

    # ---------- Warranties ----------
    @http.route(['/my/warranties', '/my/warranties/page/<int:page>'],
                type='http', auth='user', website=True)
    def my_warranties(self, page=1, **kw):
        Warranty = request.env['warranty.record']
        domain = [('partner_id', 'child_of',
                   request.env.user.partner_id.commercial_partner_id.id)]
        total = Warranty.search_count(domain)
        pager = portal_pager(url='/my/warranties', total=total, page=page, step=15)
        warranties = Warranty.search(domain, limit=15, offset=pager['offset'])
        return request.render('warranty_management.portal_my_warranties', {
            'warranties': warranties,
            'page_name': 'warranties',
            'pager': pager,
            'default_url': '/my/warranties',
        })

    @http.route('/my/warranties/<int:warranty_id>', type='http', auth='user', website=True)
    def my_warranty_detail(self, warranty_id, **kw):
        try:
            warranty = self._document_check_access('warranty.record', warranty_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        return request.render('warranty_management.portal_warranty_detail', {
            'warranty': warranty,
            'page_name': 'warranties',
        })

    # ---------- Claims ----------
    @http.route(['/my/warranty-claims', '/my/warranty-claims/page/<int:page>'],
                type='http', auth='user', website=True)
    def my_claims(self, page=1, **kw):
        Claim = request.env['warranty.claim']
        domain = [('partner_id', 'child_of',
                   request.env.user.partner_id.commercial_partner_id.id)]
        total = Claim.search_count(domain)
        pager = portal_pager(url='/my/warranty-claims', total=total, page=page, step=15)
        claims = Claim.search(domain, limit=15, offset=pager['offset'])
        return request.render('warranty_management.portal_my_claims', {
            'claims': claims,
            'page_name': 'warranty_claims',
            'pager': pager,
            'default_url': '/my/warranty-claims',
        })

    @http.route('/my/warranty-claims/<int:claim_id>', type='http', auth='user', website=True)
    def my_claim_detail(self, claim_id, **kw):
        try:
            claim = self._document_check_access('warranty.claim', claim_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        return request.render('warranty_management.portal_claim_detail', {
            'claim': claim,
            'page_name': 'warranty_claims',
        })

    @http.route('/my/warranties/<int:warranty_id>/claim', type='http',
                auth='user', website=True, methods=['GET'])
    def new_claim_form(self, warranty_id, **kw):
        try:
            warranty = self._document_check_access('warranty.record', warranty_id)
        except (AccessError, MissingError):
            return request.redirect('/my')
        return request.render('warranty_management.portal_new_claim', {
            'warranty': warranty,
            'page_name': 'warranty_claims',
            'error': kw.get('error'),
        })

    @http.route('/my/warranties/<int:warranty_id>/claim/submit', type='http',
                auth='user', website=True, methods=['POST'], csrf=True)
    def submit_claim(self, warranty_id, **post):
        try:
            warranty = self._document_check_access('warranty.record', warranty_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        description = (post.get('description') or '').strip()
        if not description:
            return request.redirect(
                f'/my/warranties/{warranty_id}/claim?error=Please describe the issue')
        if not warranty.sudo().is_valid_on(request.env['warranty.claim']
                                           ._fields['claim_date'].today()):
            return request.redirect(
                f'/my/warranties/{warranty_id}/claim?error=This warranty is no longer valid')

        claim = request.env['warranty.claim'].sudo().create({
            'warranty_id': warranty.id,
            'description': description,
            'user_id': False,
        })

        attachments = request.httprequest.files.getlist('attachments')
        attachment_ids = []
        for f in attachments:
            if not f or not f.filename:
                continue
            att = request.env['ir.attachment'].sudo().create({
                'name': f.filename,
                'datas': __import__('base64').b64encode(f.read()),
                'res_model': 'warranty.claim',
                'res_id': claim.id,
            })
            attachment_ids.append(att.id)
        if attachment_ids:
            claim.sudo().write({'attachment_ids': [(6, 0, attachment_ids)]})

        claim.sudo().message_post(
            body=_('Claim submitted from the customer portal.'),
            author_id=request.env.user.partner_id.id)
        return request.redirect(f'/my/warranty-claims/{claim.id}')