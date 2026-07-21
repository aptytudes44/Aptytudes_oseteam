# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    _order = 'name desc'

    @api.onchange('project_id')
    def _onchange_project(self):
         
        #self.analytic_account_id = self.project_id.analytic_account_id.id
        #self.analytic_account_id = self.project_id.auto_account_id.id
        
        
        if not self.partner_id:
            self.partner_id = self.project_id.partner_id.id
            if self.env.context.get('default_project_id'):
                partner = self.project_id.partner_id
                addr = partner.address_get(['delivery', 'invoice'])
                self.partner_move_id = addr['invoice']
                self.partner_shipping_id = addr['delivery']
                self.pricelist_id = (partner.property_product_pricelist
                                     and partner.property_product_pricelist.id or False)
                self.payment_term_id = (partner.property_payment_term_id
                                        and partner.property_payment_term_id.id or False)
        self.client_order_ref = self.project_id.customer_reference
        self.responsible_business_id = self.project_id.responsible_business_id.id
        self.phone_responsible_business = self.project_id.phone_responsible_business
        self.mail_responsible_business = self.project_id.mail_responsible_business

    def _still_billed(self):
        for order in self:
            amount_invoice = amount_refund = 0.0
            for invoice in order.invoice_ids:
                if invoice.state not in ('draft', 'cancel'):
                    if invoice.move_type == 'out_invoice':
                        amount_invoice += invoice.amount_untaxed
                    if invoice.move_type == 'out_refund':
                        amount_refund += invoice.amount_untaxed
            order.still_billed = order.amount_untaxed - (amount_invoice - amount_refund)

    def _order_realisation_state(self):
        for order in self:
            order.order_realisation_state = False
            last_date = datetime.strptime("2020-01-01", '%Y-%m-%d').date()
            for line in order.order_progress_line:
                if line.validation_date:
                    if line.validation_date >= last_date and line.validate:
                        order.order_realisation_state = line.name

    # v16 : action_invoice_create → _create_invoices
    def _create_invoices(self, grouped=False, final=False, date=None):
        invoices = super(SaleOrder, self)._create_invoices(grouped=grouped, final=final, date=date)
        for invoice in invoices:
            invoice.write({
                'project_id': self.project_id.id,
                'company_bank_id': self.partner_id.company_bank_id.id,
            })
        return invoices

    def _compute_sale_purchase_create(self):
        for sale in self:
            sale.sale_purchase_create = bool(sale.sale_order_purchase_ids)

    def open_sale_purchase(self):
        for sale in self:
            ids = [p.id for p in sale.sale_order_purchase_ids]
            if ids:
                return {
                    'name': _("Purchase order"),
                    'type': 'ir.actions.act_window',
                    'res_model': 'purchase.order',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', ids)],
                    'target': 'current',
                }

    def action_create_purchase_order(self):
        for sale in self:
            return {
                'name': _("Purchase order"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order',
                'view_mode': 'form',
                'context': "{'default_account_analytic_id': %s}" % sale.project_id.account_id.id,
                'target': 'current',
            }

    def _compute_sale_order_purchase_ids(self):
        for sale in self:
            if sale.project_id and sale.state not in ('draft', 'sent'):
                purchase_orders = self.env['purchase.order'].search(
                    [('account_analytic_id', '=', sale.project_id.account_id.id)])
                sale.sale_order_purchase_ids = purchase_orders
            else:
                sale.sale_order_purchase_ids = False

    def create_checklist_project_data(self):
        data_ids = self.env['quality.control.quality.cheklist.data'].search(
            [('default_data', '=', True)])
        for data in data_ids:
            if self.project_id:
                self.env['quality.control.quality.cheklist'].create({
                    'project_id': self.project_id.id,
                    'name': data.id,
                })

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for pick in self.picking_ids:
            pick.write({'project_id': self.project_id.id})
        self.env['sale.order.progress'].create({'order_id': self.id, 'name': 'customer_waiting'})
        self.env['sale.order.progress'].create({'order_id': self.id, 'name': 'study_to_be_done'})
        self.env['sale.order.progress'].create({'order_id': self.id, 'name': 'study_in_progress'})
        self.env['sale.order.progress'].create({'order_id': self.id, 'name': 'production'})
        self.env['sale.order.progress'].create({'order_id': self.id, 'name': 'on_site_assembly'})
        self.env['sale.order.progress'].create({'order_id': self.id, 'name': 'delivery'})
        self.env['sale.order.progress'].create({'order_id': self.id, 'name': 'to_bill'})
        return res

    # --- Fields ---
    # EXISTE DEJA"
    project_id = fields.Many2one('project.project', string="Project", domain="[]", check_company=False)
    project_task_ids = fields.One2many(
        related='project_id.task_ids', string='Project tasks', readonly=False)
    checklist_line_project = fields.One2many(
        related='project_id.checklist_line', string='Check List Lines', readonly=False)
    date_verification_project = fields.Date(
        related='project_id.date_verification', string="Date of verification", readonly=False)
    name_auditor_project = fields.Many2one(
        related='project_id.name_auditor', string="Name of auditor", readonly=False)
    noncompliance_line_project = fields.One2many(
        related='project_id.noncompliance_line', string='Noncompliance Lines', readonly=False)
    title_project = fields.Char(related="project_id.name", string='Business reference')
    comment_not = fields.Text('Comment')
    responsible_business_id = fields.Many2one('res.partner', string="Responsible business")
    phone_responsible_business = fields.Char(
        related='responsible_business_id.mobile', string="Phone responsible")
    mail_responsible_business = fields.Char(
        related='responsible_business_id.email', string="Mail responsible")
    technical_document = fields.Html('Technical document')
    print_technical_document = fields.Boolean('Print Technical document with the quotation')
    still_billed = fields.Float('Still to be billed', compute='_still_billed')
    sale_purchase_create = fields.Boolean(
        'Sale purchase create', compute='_compute_sale_purchase_create')
    sale_order_purchase_ids = fields.One2many(
        'purchase.order', compute='_compute_sale_order_purchase_ids',
        string="Sale Order Purchase")
    approval_deadline = fields.Date('Approval deadline')
    order_progress_line = fields.One2many(
        'sale.order.progress', 'order_id', string='Order Progress')
    order_realisation_state = fields.Selection([
        ('customer_waiting', 'Attente client'),
        ('study_to_be_done', 'Etude à faire'),
        ('study_in_progress', 'Etude en cours'),
        ('production', 'Réalisation / Accord client reçu par écrit'),
        ('on_site_assembly', 'Montage sur site'),
        ('delivery', 'Livraison'),
        ('to_bill', 'A facturer'),
    ], string='Etat Avancement', readonly=True, copy=False,
        compute='_order_realisation_state')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('price_unit', 'purchase_price', 'margin_sale_line')
    def _change_margin(self):
        if self._context.get('margin_sale_line') and self.purchase_price > 0:
            self.price_unit = self.purchase_price + (
                self.purchase_price * self.margin_sale_line / 100)
        if self._context.get('price_unit') and self.purchase_price > 0:
            self.margin_sale_line = (
                self.price_unit - self.purchase_price) / self.purchase_price * 100
        if self._context.get('purchase_price') and self.purchase_price > 0:
            self.margin_sale_line = (
                self.price_unit - self.purchase_price) / self.purchase_price * 100

    margin_sale_line = fields.Integer('Margin %')


class SaleOrderPurchaseLine(models.Model):
    _name = 'sale.order.purchase.line'
    _description = 'Sale Order Purchase Line'
    _order = 'on_stock'

    @api.onchange('product_id')
    def _product_onchange(self):
        if self.product_id:
            complete_name = ''
            if self.product_id.default_code:
                complete_name = '[' + str(self.product_id.default_code) + '] '
            complete_name += str(self.product_id.name)
            if self.product_id.description_purchase:
                complete_name += '\n' + str(self.product_id.description_purchase)
            self.name = complete_name
            self.product_uom = self.product_id.product_tmpl_id.uom_po_id.id

    def _compute_ordered_qty(self):
        for line in self:
            qty = 0.0
            for pl in line.sale_purchase_lines:
                if pl.state != 'cancel':
                    qty += pl.product_qty
            line.product_order_qty = qty

    def _compute_received_qty(self):
        for line in self:
            qty = 0.0
            for pl in line.sale_purchase_lines:
                if pl.state != 'cancel':
                    qty += pl.qty_received
            line.product_received_qty = qty

    order_id = fields.Many2one('sale.order', string='Order Reference',
                               required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('purchase_ok', '=', True), ('type', '!=', 'service')])
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    product_uom_qty = fields.Float(string='Qty to order', default=1.0)
    product_order_qty = fields.Float(string='Ordered qty', compute='_compute_ordered_qty')
    product_received_qty = fields.Float(string='Received qty', compute='_compute_received_qty')
    on_stock = fields.Boolean('On stock')
    sale_purchase_lines = fields.Many2many(
        'purchase.order.line', 'sale_purchase_lines_rel',
        'sale_order_purchase_line_id', 'purchase_line_id',
        string='Purchase Lines', copy=False)

    def unlink(self):
        for line in self:
            if line.sale_purchase_lines:
                raise UserError(_('You cannot delete a purchase line with a pending order!'))
        return super(SaleOrderPurchaseLine, self).unlink()


class SaleOrderProgress(models.Model):
    _name = 'sale.order.progress'
    _description = 'Sale Order Progress'

    @api.onchange('validate')
    def _validate_onchange(self):
        if self.validate:
            self.validation_date = fields.Date.to_string(datetime.now())
        else:
            self.validation_date = False

    order_id = fields.Many2one('sale.order', string='Order Reference',
                               required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Selection([
        ('customer_waiting', 'Customer waiting'),
        ('study_to_be_done', 'Study to be done'),
        ('study_in_progress', 'Study in progress'),
        ('production', 'Production / Customer Agreement'),
        ('on_site_assembly', 'On site assembly'),
        ('delivery', 'Delivery'),
        ('to_bill', 'To bill'),
    ], string='Step', readonly=False, copy=False, default='customer_waiting')
    validate = fields.Boolean('Validate')
    validation_date = fields.Date('Validation date')
