from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'
        
    access_token = fields.Char(
        string="Security Token",
        copy=False,
        index=True,
        readonly=True,
    )

    signature_picking = fields.Binary(
        string="Signature du bon de livraison",
        copy=False,
        readonly=True,
    )
    signed = fields.Boolean(
        string="Signé",
        default=False,
        copy=False,
        readonly=True,
    )
    signature_date = fields.Datetime(
        string="Date de signature",
        copy=False,
        readonly=True,
    )
    signed_by = fields.Char(
        string="Signé par",
        copy=False,
        readonly=True,
    )

    signature_status = fields.Selection(
        selection=[
            ('non_signe', 'Non signé'),
            ('signe', 'Signé'),
        ],
        string="Signature",
        compute='_compute_signature_status',
        store=False,
        readonly=True,
    )

    @api.depends('signed')
    def _compute_signature_status(self):
        for picking in self:
            picking.signature_status = 'signe' if picking.signed else 'non_signe'
            
    @api.model
    def create(self, vals):
        picking = super().create(vals)
        if not picking.access_token:
            picking.access_token = self.env['ir.config_parameter'].sudo().get_param('database.uuid') + '-' + str(picking.id)
        return picking

    def action_send_signature_link(self):
        """Ouvre la fenêtre de messagerie avec un bouton 'Signer' dans l'email"""
        self.ensure_one()
        if self.picking_type_code != 'outgoing':
            return False

        # Récupère le template de mail
        template = self.env.ref('stock_picking_signature.mail_template_signature_link', raise_if_not_found=False)
        if not template:
            raise UserError("Le template de mail 'Livraison : Signature des BL en ligne' n'existe pas.")

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_model': 'stock.picking',
                'default_res_ids': [self.id],
                'default_template_id': template.id,
                'default_use_template': True,
                'default_composition_mode': 'comment',
                'force_email': True,
                'default_partner_ids': [(4, self.partner_id.id)] if self.partner_id else False,
            },
        }

        
    def action_preview_signature(self):
        self.ensure_one()
        if self.picking_type_code != 'outgoing':
            return False
        return {
            'type': 'ir.actions.act_url',
            'url': f'/stock/picking/{self.id}/sign',
            'target': 'new',
        }

    def get_signature_link(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/stock/picking/{self.id}/sign"
