# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Champ technique (pas affiché sur les documents) permettant d'identifier
    # les produits "fourre-tout" derrière lesquels se trouvent, dans le devis,
    # les vraies lignes de note décrivant le travail. Voir
    # sale.order._fill_generic_product_delivery_description.
    bl_generic_product = fields.Boolean(
        string="Produit générique BL",
        help="Si coché : à la confirmation du devis, le texte des lignes de "
             "note qui suivent ce produit est repris automatiquement sous le "
             "nom du produit sur le bon de livraison.")
