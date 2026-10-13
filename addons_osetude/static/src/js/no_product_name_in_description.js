/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductLabelSectionAndNoteField } from "@account/components/product_label_section_and_note_field/product_label_section_and_note_field";
import { SaleOrderLineProductField } from "@sale/js/sale_product_field";

// Le widget natif (utilisé par les lignes de devis/commandes de vente ET d'achat)
// reconstruit "NomDuProduit\nTexte" à chaque frappe dans la description via updateLabel().
// On ne veut jamais le nom du produit dans la description : on garde juste le texte saisi.
//
// A l'affichage, le natif retire le nom du produit N'IMPORTE OU dans la description
// (label.replace(productName, "")) : "Etudes pour test" devenait "pour test" et, comme
// updateLabel() ci-dessous sauvegarde le texte affiche tel quel, la troncature finissait
// en base. On ne retire le nom que s'il constitue toute la description ou s'il est en tete
// suivi d'un saut de ligne (ancien format auto-genere "Nom\nTexte").
function stripProductName(label, productName) {
    label = label || "";
    if (!productName) {
        return label;
    }
    if (label === productName) {
        return "";
    }
    if (label.startsWith(productName + "\n")) {
        return label.slice(productName.length + 1);
    }
    return label;
}

patch(ProductLabelSectionAndNoteField.prototype, {
    get label() {
        return stripProductName(this.props.record.data.name, this.productName);
    },
    updateLabel(value) {
        this.props.record.update({ name: value || "" });
    },
});

// Les lignes de devis/commandes de VENTE utilisent un widget spécifique
// (SaleOrderLineProductField, sol_product_many2one) qui redéfinit SA PROPRE version de
// updateLabel() en se basant sur "translated_product_name" : le patch ci-dessus sur la classe
// parente ne suffit pas, il faut surcharger cette classe fille aussi.
patch(SaleOrderLineProductField.prototype, {
    get label() {
        return stripProductName(
            this.props.record.data.name, this.translatedProductName || this.productName
        );
    },
    updateLabel(value) {
        this.props.record.update({ name: value || "" });
    },
});
