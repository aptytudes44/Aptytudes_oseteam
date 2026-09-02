/** @odoo-module **/

// Sur les lignes de commande d'achat/vente (widget natif
// product_label_section_and_note_field), le champ Produit et la Description
// partagent la même cellule/colonne technique ("name" est retiré des
// colonnes actives par ProductLabelSectionAndNoteListRender.getActiveColumns
// dans le module account). Résultat : le premier clic sur une ligne, même
// sur le texte de la description déjà affichée, ouvre toujours la ligne en
// focalisant le champ Produit (onCellClicked ne connaît que la colonne
// "product_id"). Il faut alors recliquer sur la description pour l'éditer.
//
// Ce patch ne touche pas à la logique interne d'Odoo : il observe le clic
// natif sur le textarea de description, laisse le comportement standard
// ouvrir la ligne, puis reprend le focus sur ce même textarea juste après
// (quelques frames d'animation, le temps que la ligne passe en édition).
// Une ligne neuve sans description n'a pas de textarea affiché (aucun
// texte à montrer tant qu'aucun produit n'est choisi) : le comportement
// natif (focus Produit) reste donc inchangé dans ce cas.

function focusDescriptionTextarea(cell, attemptsLeft = 12) {
    const row = cell.closest("tr");
    if (row && row.classList.contains("o_selected_row")) {
        const textarea = cell.querySelector("textarea");
        if (textarea) {
            textarea.focus();
            const pos = textarea.value.length;
            textarea.setSelectionRange(pos, pos);
            return;
        }
    }
    if (attemptsLeft > 0) {
        requestAnimationFrame(() => focusDescriptionTextarea(cell, attemptsLeft - 1));
    }
}

document.addEventListener(
    "click",
    (ev) => {
        if (ev.target.tagName !== "TEXTAREA") {
            return;
        }
        const cell = ev.target.closest(".o_field_product_label_section_and_note_cell");
        if (!cell) {
            return;
        }
        // Limité aux lignes de commande (achats/ventes) : champ order_line.
        if (!cell.closest('[name="order_line"]')) {
            return;
        }
        const row = cell.closest("tr");
        if (row && row.classList.contains("o_selected_row")) {
            // Ligne déjà en édition : le clic natif sur le textarea suffit.
            return;
        }
        focusDescriptionTextarea(cell);
    },
    true
);
