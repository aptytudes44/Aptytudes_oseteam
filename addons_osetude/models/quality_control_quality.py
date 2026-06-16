# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

# Plage d'années pour le champ quality_year (à mettre à jour si nécessaire)
YEAR_RANGE = [(str(num), str(num)) for num in range(2017, 2031)]


class QualityControlQuality(models.Model):
    _name = "quality.control.quality"
    _description = "Quality control"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'supplier_id, quality_year desc'

    @api.onchange('supplier_id','quality_year')
    def _compute_complete_name(self):
        for line in self:
            if line.supplier_id.name:
                line.name = str(line.quality_year) + " - " + line.supplier_id.name
            else:
                line.name = str(line.quality_year)
                
    @api.depends('service_quality', 'price_competitiveness', 'deadlines',
                 'product_quality_services', 'conformity_of_deliveries')
    def _compute_supplier_note(self):
        for rec in self:
            if rec.is_supplier_selection == 'notation':
                rec.supplier_note = (rec.service_quality + rec.price_competitiveness
                                     + rec.deadlines + rec.product_quality_services
                                     + rec.conformity_of_deliveries)
            else:
                rec.supplier_note = 0

    @api.depends('location', 'price_competitiveness', 'deadlines',
                 'product_quality_services', 'relational')
    def _compute_supplier_selection_score(self):
        for rec in self:
            if rec.is_supplier_selection == 'selection':
                rec.supplier_selection_score = (rec.relational + rec.price_competitiveness
                                                + rec.deadlines + rec.product_quality_services
                                                + rec.location)
            else:
                rec.supplier_selection_score = 0

    @api.depends('supplier_id.is_subcontractor')
    def _compute_supplier_type(self):
        for rec in self:
            rec.supplier_type = ('subcontractor'
                                 if rec.supplier_id.is_subcontractor else 'supplier')

    @api.model_create_multi
    def create(self, vals_list):
        results = super(QualityControlQuality, self).create(vals_list)
        try:
            params = self.env['quality.control.parameters'].search([('id', '=', 1)])
            for result in results:
                if params:
                    if result.is_supplier_selection == 'selection':
                        result.write({
                            'scale_binary': params.selection_binary_model,
                            'scale_filename': params.selection_binary_model_filename,
                        })
                    else:
                        result.write({
                            'scale_binary': params.quotation_binary_model,
                            'scale_filename': params.quotation_binary_model_filename,
                        })
        except Exception:
            raise UserError(_('No scale parameters found !'))
        return results

    name = fields.Char("Quality control", required=True, compute="_compute_complete_name", store=True)
    supplier_id = fields.Many2one('res.partner', string="Supplier", domain=[('is_company', '=', True), ('supplier_rank', '>', 0)])
    supplier_contact_id = fields.Many2one('res.partner', string="Contact", domain=[('is_company', '=', False), ('supplier_rank', '>', 0)])
    supplier_contact_email = fields.Char(related='supplier_contact_id.email', string="Email")
    supplier_contact_phone = fields.Char(related='supplier_contact_id.phone', string="Phone")
    supplier_contact_mobile = fields.Char(related='supplier_contact_id.mobile', string="Mobile")
    quality_year = fields.Selection(YEAR_RANGE, default=str(fields.Date.today().year), string='Year')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    service_quality = fields.Integer('Service quality')
    price_competitiveness = fields.Integer('Price competitiveness')
    deadlines = fields.Integer('Deadlines')
    product_quality_services = fields.Integer('Product quality/Services')
    conformity_of_deliveries = fields.Integer('Conformity of deliveries')
    Comment = fields.Text('Comment')
    corrective_actions = fields.Text('Corrective actions')
    supplier_note = fields.Integer('Global mark', compute='_compute_supplier_note', store=True)
    is_supplier_selection = fields.Selection([
        ('selection', 'SELECTION'),
        ('notation', 'NOTATION'),
    ], 'Is Supplier selection')
    supplier_selection_score = fields.Integer(
        'Global mark', compute='_compute_supplier_selection_score', store=True)
    location = fields.Integer('Supplier location')
    relational = fields.Integer('Relational')
    supplier_type = fields.Selection([
        ('supplier', 'Supplier'),
        ('subcontractor', 'Subcontractor')],
        'Supplier type', compute='_compute_supplier_type', store=True)
    scale_filename = fields.Char("Scale filename")
    scale_binary = fields.Binary('Scale File')


class QualityControlParameters(models.Model):
    _name = "quality.control.parameters"
    _description = "Quality control parameters"

    selection_binary_model = fields.Binary('Selection binary model')
    selection_binary_model_filename = fields.Char('Selection binary model filename')
    quotation_binary_model = fields.Binary('Quotation binary model')
    quotation_binary_model_filename = fields.Char('Quotation binary model filename')


class QualityControlQualityChecklist(models.Model):
    _name = "quality.control.quality.cheklist"
    _description = "Quality control Check List"

    project_id = fields.Many2one('project.project', string='Project Reference',
                                  required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Many2one('quality.control.quality.cheklist.data',
                            string="Name", required=True)
    checked = fields.Boolean('Checked')
    applicable = fields.Boolean('Applicable')


class QualityControlQualityChecklistData(models.Model):
    _name = "quality.control.quality.cheklist.data"
    _description = "Quality control Check List Data"
    _order = 'id, sequence'

    name = fields.Char('Name', required=True)
    sequence = fields.Integer('Sequence', default=10)
    default_data = fields.Boolean('Default')


class QualityControlQualityNoncompliance(models.Model):
    _name = "quality.control.quality.noncompliance"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Quality control Noncompliance"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/.....':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'quality.control.quality.noncompliance')
        return super(QualityControlQualityNoncompliance, self).create(vals_list)

    @api.onchange('imputation')
    def _onchange_imputation(self):
        if self.imputation in ('supplier', 'internal'):
            self.partner_id = False
        if self.imputation == 'customer':
            self.partner_id = self.project_id.partner_id.id

    @api.onchange('type')
    def _ochange_type(self):
        if self.type == 'noncompliance':
            self.imputation = 'internal'
        if self.type == 'claim':
            self.imputation = 'supplier'
        if self.type == 'after_sales_service':
            self.imputation = 'customer'

    project_id = fields.Many2one('project.project', string='Project Reference',
                                  required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Char("Number", required=True, default="/.....")
    type = fields.Selection([
        ('noncompliance', 'Internal noncompliance'),
        ('claim', 'Claim'),
        ('after_sales_service', 'After sales service'),
    ], 'Type', required=True)
    imputation = fields.Selection([
        ('internal', 'Internal'),
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
    ], 'Imputation', required=True)
    state = fields.Selection([
        ('1', 'To be transmitted to the quality department'),
        ('2', 'Awaiting Customer / Supplier validation'),
        ('3', 'Corrective action in progress'),
        ('4', 'Close'),
    ], 'State', required=True, default='1')
    partner_id = fields.Many2one('res.partner', string="Third Party Concerned")
    sale_id = fields.Many2one('sale.order', string="Sale order")
    purchase_id = fields.Many2one('purchase.order', string="Purchase order")
    user_id = fields.Many2one('res.users', string="From")
    date_of_issue = fields.Date('Date of issue')
    close_date = fields.Date('Close date')
    noncompliance_cause_id = fields.Many2one(
        'quality.control.quality.noncompliance.cause', string="Cause")
    severity_level = fields.Selection([
        ('1', 'Benign'),
        ('3', 'Significant'),
        ('4', 'Grave'),
    ], 'Severity level')
    noncompliant_note = fields.Text('Description')
    immediate_correction_note = fields.Text('Description immediate correction')
    description_correction = fields.Text('Description correction')
    description_cause = fields.Text('Description cause')
    measure_effectiveness_correction = fields.Text(
        'Measure of the effectiveness of the correction')
    # v16 : _company_default_get → self.env.company
    company_id = fields.Many2one('res.company', 'Company',
                                  default=lambda self: self.env.company)
    currency_id = fields.Many2one("res.currency", related='company_id.currency_id',
                                   string="Currency", readonly=True)
    study = fields.Monetary('Study')
    production = fields.Monetary('Production')
    comment = fields.Text('Comment')
    root_causes = fields.Text('Root causes')
    root_causes_filename = fields.Char("Root causes filename")
    root_causes_binary = fields.Binary('File')


class QualityControlQualityNoncomplianceCause(models.Model):
    _name = "quality.control.quality.noncompliance.cause"
    _description = "Quality control Noncompliance Cause"
    _order = 'id, sequence'

    name = fields.Char("Name", required=True)
    sequence = fields.Integer('Sequence', default=10)
