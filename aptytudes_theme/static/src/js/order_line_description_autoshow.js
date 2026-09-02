/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useEffect } from "@odoo/owl";
import { ProductLabelSectionAndNoteField } from "@account/components/product_label_section_and_note_field/product_label_section_and_note_field";

// Par defaut (widget natif), le textarea de description sur une ligne de
// commande reste masque tant que l'utilisateur ne clique pas sur l'icone
// "3 traits" (labelVisibilityButtonId), meme juste apres avoir choisi un
// produit. On l'affiche automatiquement des qu'un produit vient d'etre
// selectionne sur la ligne (transition "pas de produit" -> "produit"),
// sans description existante — pas au premier rendu d'une ligne deja
// enregistree (sinon toutes les lignes sans description s'ouvriraient en
// permanence, y compris celles ou l'utilisateur n'en veut pas).
patch(ProductLabelSectionAndNoteField.prototype, {
    setup() {
        super.setup();
        let isFirstRun = true;
        let hadProduct = this._hasProductValue();
        useEffect(
            () => {
                const hasProduct = this._hasProductValue();
                if (!isFirstRun && !hadProduct && hasProduct && !this.label) {
                    this.labelVisibility.value = true;
                }
                hadProduct = hasProduct;
                isFirstRun = false;
            },
            () => [this._hasProductValue()]
        );
    },

    _hasProductValue() {
        const value = this.props.record.data[this.props.name];
        return !!(value && value[0]);
    },
});
