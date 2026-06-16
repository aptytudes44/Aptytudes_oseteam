# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CreatePurchaseOrder(models.TransientModel):
    _name = 'create.purchase_order'
    _description = 'Create purchase order'

    @api.model
    def default_get(self, fields_list):
        res = super(CreatePurchaseOrder, self).default_get(fields_list)
        active_ids = self.env.context.get('active_ids')
        order = self.env['sale.order'].browse(active_ids)
        if not order.order_purchase_line:
            raise ValidationError(
                _('You must enter purchasing lines to be able to generate a price request!'))
        new_lines = []
        for line in order.order_purchase_line:
            if not line.on_stock:
                prod_order = line.product_uom_qty - line.product_order_qty
                if prod_order > 0:
                    new_lines.append((0, 0, {
                        'sale_order_purchase_line_id': line.id,
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': prod_order,
                        'product_order_qty': line.product_order_qty,
                    }))
        res['order_purchase_product_line'] = new_lines
        res['order_id'] = order.id
        res['reception_desired_on'] = order.approval_deadline
        return res

    def create_purchase_order(self):
        if not self.order_purchase_product_line:
            raise ValidationError(
                _('You must enter purchasing lines to be able to generate a price request!'))
        # v17 : account_analytic_id kept on purchase.order header (custom field)
        # purchase.order.line uses analytic_distribution (JSON) instead
        analytic_id = self.order_id.analytic_account_id.id
        analytic_distribution = {str(analytic_id): 100} if analytic_id else {}
        purchase_order = self.env['purchase.order'].create({
            'user_id': self.env.uid,
            'origin': self.order_id.name,
            'partner_id': self.supplier_id.id,
            'account_analytic_id': analytic_id,
        })
        for line in self.order_purchase_product_line:
            existing_ids = line.sale_order_purchase_line_id.sale_purchase_lines.ids[:]
            purchase_line = self.env['purchase.order.line'].create({
                'order_id': purchase_order.id,
                'name': line.sale_order_purchase_line_id.name,
                'product_id': line.sale_order_purchase_line_id.product_id.id,
                'product_qty': line.product_uom_qty,
                'product_uom': line.sale_order_purchase_line_id.product_id.uom_po_id.id,
                'price_unit': line.sale_order_purchase_line_id.product_id.standard_price,
                'date_planned': self.reception_desired_on,
                'taxes_id': [(6, 0, line.product_id.supplier_taxes_id.ids)],
                'analytic_distribution': analytic_distribution,
            })
            existing_ids.append(purchase_line.id)
            line.sale_order_purchase_line_id.write({
                'sale_purchase_lines': [(6, 0, existing_ids)],
            })
        return {
            'name': _("Purchase order"),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id,
            'target': 'current',
        }

    # v16 : domain supplier_rank
    supplier_id = fields.Many2one('res.partner', string="Supplier",
                                   domain=[('supplier_rank', '>', 0)])
    reception_desired_on = fields.Date('Reception desired on')
    order_id = fields.Many2one('sale.order', string="Sale Order")
    order_purchase_product_line = fields.One2many('create.purchase.order.line', 'purchase_line_id', string='Purchase Lines')


class CreatePurchaseOrderLine(models.TransientModel):
    _name = 'create.purchase.order.line'
    _description = 'Create Purchase Order Line'

    purchase_line_id = fields.Many2one('create.purchase_order',
                                        string='Sale purchase lines', ondelete='cascade')
    sale_order_purchase_line_id = fields.Many2one(
        'sale.order.purchase.line', string="Sale Order Line")
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Text(string='Description')
    product_uom_qty = fields.Float(string='Qty to order')
    product_order_qty = fields.Float(string='Ordered qty')
