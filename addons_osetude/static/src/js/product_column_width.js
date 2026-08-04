/** @odoo-module **/

import { saleOrderLineProductField } from "@sale/js/sale_product_field";

// Le widget de la colonne Produit des lignes de devis/commandes de vente a une largeur
// max codée en dur à 400px (héritée de productLabelSectionAndNoteField), ce qui empêche
// la colonne de s'étendre pour occuper l'espace disponible une fois les autres colonnes
// (Taxes, Répartition analytique...) fixées. On retire ce plafond : min 240px, pas de max,
// pour que le mécanisme natif de calcul des largeurs de colonnes lui attribue l'espace restant.
saleOrderLineProductField.listViewWidth = [240, 99999];
