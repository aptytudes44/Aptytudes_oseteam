/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductLabelSectionAndNoteField } from "@account/components/product_label_section_and_note_field/product_label_section_and_note_field";
import { SaleOrderLineProductField } from "@sale/js/sale_product_field";

// Le widget natif (utilisé par les lignes de devis/commandes de vente ET d'achat)
// reconstruit "NomDuProduit\nTexte" à chaque frappe dans la description via updateLabel().
// On ne veut jamais le nom du produit dans la description : on garde juste le texte saisi.
patch(ProductLabelSectionAndNoteField.prototype, {
    updateLabel(value) {
        this.props.record.update({ name: value || "" });
    },
});

// Les lignes de devis/commandes de VENTE utilisent un widget spécifique
// (SaleOrderLineProductField, sol_product_many2one) qui redéfinit SA PROPRE version de
// updateLabel() en se basant sur "translated_product_name" : le patch ci-dessus sur la classe
// parente ne suffit pas, il faut surcharger cette classe fille aussi.
patch(SaleOrderLineProductField.prototype, {
    updateLabel(value) {
        this.props.record.update({ name: value || "" });
    },
});
