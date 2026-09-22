# -*- coding: utf-8 -*-
import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = "Purchase Order"

    def _compute_qty_ordered(self):
        for order in self:
            order.qty_ordered = sum(l.product_qty for l in order.order_line)

    def _compute_qty_received(self):
        for order in self:
            order.qty_received = sum(l.qty_received for l in order.order_line)

    def _compute_qty_to_receive(self):
        for order in self:
            order.qty_to_receive = sum(
                (l.product_qty - l.qty_received) for l in order.order_line)

    def write(self, values):
        res = super(PurchaseOrder, self).write(values)
        if values.get('state') == 'purchase':
            quality_search = self.env['quality.control.quality'].search([
                ('supplier_id', '=', self.partner_id.id),
                ('quality_year', '=', datetime.datetime.now().strftime("%Y")),
            ])
            if not quality_search:
                self.env['quality.control.quality'].create({
                    'name': datetime.datetime.now().strftime("%Y") + " - " + self.partner_id.name,
                    'supplier_id': self.partner_id.id,
                    'supplier_contact_id': self.partner_id.id,
                    'supplier_contact_email': self.partner_id.email,
                    'supplier_contact_phone': self.partner_id.phone,
                    'supplier_contact_mobile': self.partner_id.mobile,
                    'quality_year': datetime.datetime.now().strftime("%Y"),
                    'company_id': self.partner_id.company_id.id,
                    'is_supplier_selection': 'notation',
                })
        return res

    @api.onchange('project_id')
    def _onchange_project_id_analytic_account(self):
        # Pre-remplit l'analytique par defaut depuis le projet, seulement si
        # elle n'est pas deja renseignee (ne pas ecraser une saisie manuelle).
        if self.project_id and not self.account_analytic_id:
            self.account_analytic_id = self.project_id.account_id

    account_analytic_id = fields.Many2one(
        'account.analytic.account', string="Default Analytic Account")
    title_project = fields.Char(
        related="project_id.title_project", string="Référence projet")
    technical_document = fields.Html('Technical document')
    print_technical_document = fields.Boolean(
        'Print Technical document with the price request')
    partner_ref_note = fields.Char('Supplier information')
    qty_ordered = fields.Float('Qty ordered', compute="_compute_qty_ordered")
    qty_received = fields.Float('Qty received', compute="_compute_qty_received")
    qty_to_receive = fields.Float('Qty to receive', compute="_compute_qty_to_receive")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _description = 'Purchase Order Line'

    @api.onchange('product_id')
    def _default_analytic_account(self):
        # v17 : account_analytic_id removed from purchase.order.line
        # → replaced by analytic_distribution (JSON dict)
        if self.order_id.account_analytic_id:
            analytic_id = self.order_id.account_analytic_id.id
            self.analytic_distribution = {str(analytic_id): 100}

    analytic_account_display_name = fields.Char(
        compute='_compute_analytic_account_display_name',
        string="Analytic Account")

    @api.depends('analytic_distribution')
    def _compute_analytic_account_display_name(self):
        AnalyticAccount = self.env['account.analytic.account']
        for line in self:
            ids = []
            for key in (line.analytic_distribution or {}):
                if key.isdigit():
                    ids.append(int(key))
            line.analytic_account_display_name = ', '.join(AnalyticAccount.browse(ids).mapped('name'))

    def _get_product_purchase_description(self, product_lang):
        # Ne jamais préfixer par le nom du produit : uniquement la description d'achat.
        return product_lang.description_purchase or ''

    description_only = fields.Text(
        string='Description only', compute='_compute_description_only')

    @api.depends('name', 'product_id')
    def _compute_description_only(self):
        for line in self:
            name = line.name or ''
            product_name = line.product_id.display_name if line.product_id else False
            if product_name and name.split('\n', 1)[0] == product_name:
                parts = name.split('\n', 1)
                line.description_only = parts[1] if len(parts) > 1 else ''
            else:
                line.description_only = name
