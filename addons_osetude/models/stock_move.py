# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    # Champ éditable à l'écran, mais qui n'affiche/n'écrit jamais le nom du
    # produit tout seul (même logique que le PDF, cf _get_report_description_picking) :
    # vide si aucune description distincte, sinon la description avec le nom
    # produit retiré en préfixe s'il y était.
    description_picking_display = fields.Text(
        string='Description',
        compute='_compute_description_picking_display',
        inverse='_inverse_description_picking_display')

    def _compute_description_picking_display(self):
        for move in self:
            move.description_picking_display = move._get_report_description_picking() or False

    def _inverse_description_picking_display(self):
        for move in self:
            move.description_picking = move.description_picking_display

    analytic_distribution = fields.Json(
        related='purchase_line_id.analytic_distribution',
        string='Répartition analytique')
    # Requis par le widget "analytic_distribution" (fieldDependencies JS), non
    # fourni par stock.move nativement (contrairement aux modèles héritant de
    # analytic.mixin, ex. purchase.order.line) : provoque une RPC_ERROR
    # ("Invalid field 'analytic_precision'") sans ce champ.
    analytic_precision = fields.Integer(
        store=False,
        default=lambda self: self.env['decimal.precision'].precision_get("Percentage Analytic"))
