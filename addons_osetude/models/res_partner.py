# -*- coding: utf-8 -*-
import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    def _quality_control_count(self):
        for line in self:
            quality = self.env['quality.control.quality'].search([
                ('supplier_id', '=', line.id),
                ('quality_year', '=', str(fields.Date.today().year)),
                ('is_supplier_selection', '=', 'notation'),
            ], limit=1)
            line.quality_control_count = quality.supplier_note if quality else 0

    def _supplier_selection_score(self):
        for line in self:
            quality = self.env['quality.control.quality'].search([
                ('supplier_id', '=', line.id),
                ('is_supplier_selection', '=', 'selection'),
            ], limit=1)
            line.supplier_selection_score = quality.supplier_selection_score if quality else 0

    def action_view_quality_control_lines(self):
        for line in self:
            vals = line.parent_id.id if line.parent_id else line.id
            return {
                'name': _("Quality control"),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.control.quality',
                'view_mode': 'tree,form',
                'context': {
                    'default_supplier_id': vals,
                    'default_is_supplier_selection': 'notation',
                },
                'domain': [('supplier_id', '=', vals),
                            ('is_supplier_selection', '=', 'notation')],
                'target': 'current',
            }

    def action_view_quality_control_lines_selection(self):
        for line in self:
            vals = line.parent_id.id if line.parent_id else line.id
            return {
                'name': _("Notation score"),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.control.quality',
                'view_mode': 'tree,form',
                'context': {
                    'default_supplier_id': vals,
                    'default_is_supplier_selection': 'selection',
                },
                'domain': [('supplier_id', '=', vals),
                            ('is_supplier_selection', '=', 'selection')],
                'target': 'current',
            }

    @api.onchange('supplier_rank')
    def _onchange_supplier(self):
        # v16 : 'supplier' field → 'supplier_rank'
        if self.supplier_rank == 0:
            self.is_subcontractor = False

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Partner, self).create(vals_list)
        for partner in res:
            # v16 : supplier_rank > 0 remplace supplier == True
            if partner.supplier_rank > 0 and partner.company_type == 'company':
                quality_search = self.env['quality.control.quality'].search(
                    [('supplier_id', '=', partner.id)])
                if not quality_search:
                    self.env['quality.control.quality'].create({
                        'name': datetime.datetime.now().strftime("%Y") + " - " + partner.name,
                        'supplier_id': partner.id,
                        'supplier_contact_id': partner.id,
                        'supplier_contact_email': partner.email,
                        'supplier_contact_phone': partner.phone,
                        'supplier_contact_mobile': partner.mobile,
                        'quality_year': datetime.datetime.now().strftime("%Y"),
                        'company_id': partner.company_id.id,
                        'is_supplier_selection': 'selection',
                    })
        return res

    company_bank_id = fields.Many2one(
        'account.journal', string="Company Bank", domain=[('type', '=', 'bank')])
    quality_control_count = fields.Integer(
        compute='_quality_control_count', string="Quality control")
    supplier_selection_score = fields.Integer(
        compute='_supplier_selection_score', string="Selection score")
    is_subcontractor = fields.Boolean(string='is a subcontractor')
    mobile = fields.Char(string="Mobile")
    
    
    
    
    
