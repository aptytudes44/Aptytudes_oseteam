from odoo import http, fields, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
import binascii

class StockPickingPortal(http.Controller):

    def _document_check_access(self, model, document_id, access_token=None):
        """Vérifie l'accès au document (comme dans les devis)"""
        document = request.env[model].browse(document_id).sudo().exists()
        if not document:
            raise MissingError("Document not found")
        if access_token and document.access_token != access_token:
            raise AccessError("Invalid access token")
        return document

    @http.route('/stock/picking/<int:picking_id>/sign', type='http', auth='public', website=True)
    def portal_picking_sign(self, picking_id, access_token=None, **kwargs):
        """Page de signature du bon de livraison"""
        try:
            picking_sudo = self._document_check_access('stock.picking', picking_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        return request.render(
            'stock_picking_signature.stock_picking_portal_template',
            {
                'picking': picking_sudo,
                'csrf_token': request.csrf_token(),
            }
        )

    @http.route('/stock/picking/<int:picking_id>/sign/submit', type='json', auth='public', website=True)
    def portal_picking_sign_submit(self, picking_id, access_token=None, name=None, signature=None, **kwargs):
        """Soumission de la signature"""
        access_token = access_token or request.httprequest.args.get('access_token')

        try:
            picking_sudo = self._document_check_access('stock.picking', picking_id, access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Bon de livraison introuvable.')}

        if not signature:
            return {'error': _('La signature est manquante.')}

        try:
            picking_sudo.write({
                'signed_by': name,
                'signature_date': fields.Datetime.now(),
                'signature_picking': signature,
                'signed': True,
            })
            request.env.cr.flush()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Données de signature invalides.')}

        # ✅ Redirige vers la page de confirmation avec le bon ID
        return {
            'force_refresh': True,
            'redirect_url': f'/stock/picking/{picking_id}/sign/confirmation',
        }

    @http.route('/stock/picking/<int:picking_id>/sign/confirmation', type='http', auth='public', website=True)
    def portal_picking_sign_confirmation(self, picking_id, access_token=None, **kwargs):
        """Page de confirmation après signature"""
        try:
            picking_sudo = self._document_check_access('stock.picking', picking_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        return request.render(
            'stock_picking_signature.signature_confirmation',
            {
                'picking': picking_sudo,
            }
        )
