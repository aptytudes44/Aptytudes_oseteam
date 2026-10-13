# -*- coding: utf-8 -*-
from odoo import fields, models


def _strip_product_name(description, *names):
    # Le natif retire le nom produit dès que la description commence par lui
    # ("Etudes pour test" -> "pour test"). On ne le retire que s'il occupe toute
    # la description ou toute la première ligne ("Etudes\nReste") : même règle
    # que la saisie vente/achat (sale_order.py, no_product_name_in_description.js).
    description = description or ''
    for name in names:
        if not name:
            continue
        if description.strip() == name:
            return ''
        if description.startswith(name + '\n'):
            return description[len(name) + 1:].strip()
    return description


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_report_description_picking(self):
        self.ensure_one()
        return _strip_product_name(self.description_picking, self.product_id.display_name)

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


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # PDF BL/BR validé (lignes regroupées) : même troncature native que
    # _get_report_description_picking, corrigée de la même façon.
    def _get_aggregated_properties(self, move_line=False, move=False):
        res = super()._get_aggregated_properties(move_line=move_line, move=move)
        move = res['move']
        product = move.product_id
        description = _strip_product_name(
            self._get_aggregated_description(move), product.display_name, product.name)
        res['description'] = description
        res['line_key'] = self._get_aggregated_line_key(move, product, res['product_uom'], description)
        return res
