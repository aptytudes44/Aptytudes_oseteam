# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PurchaseOrderAddLinesBulk(models.TransientModel):
    _name = 'purchase.order.add.lines.bulk'
    _description = "Ajouter un produit en masse sur une demande d'achat"

    def _default_account_analytic_id(self):
        order = self.env['purchase.order'].browse(self.env.context.get('default_order_id'))
        return order.account_analytic_id

    order_id = fields.Many2one('purchase.order', string='Commande', required=True)
    product_id = fields.Many2one(
        'product.product', string='Produit', required=True,
        domain=[('purchase_ok', '=', True)])
    product_qty = fields.Float(string='Quantité par ligne', default=1.0, required=True)
    line_count = fields.Integer(string='Nombre de lignes', default=1, required=True)
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Analytique',
        default=_default_account_analytic_id)

    def action_add_lines(self):
        self.ensure_one()
        analytic_distribution = (
            {str(self.account_analytic_id.id): 100} if self.account_analytic_id else False)
        vals_list = [{
            'order_id': self.order_id.id,
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'name': 'A renseigner',
            'analytic_distribution': analytic_distribution,
        } for _ in range(self.line_count)]
        self.env['purchase.order.line'].create(vals_list)
        return {'type': 'ir.actions.act_window_close'}
