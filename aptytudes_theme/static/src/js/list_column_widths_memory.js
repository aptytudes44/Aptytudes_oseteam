/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useEffect } from "@odoo/owl";

// Odoo natif ne memorise jamais les largeurs de colonnes redimensionnees a
// la souris : column_width_hook.js (module web) stocke la largeur calculee
// uniquement dans une variable de fermeture JS, perdue au moindre
// rechargement de page ou changement de vue (verifie dans le code source,
// aucun appel a localStorage/serveur). Ce patch les sauvegarde dans le
// localStorage du navigateur (donc par poste/navigateur, pas partage entre
// utilisateurs ni entre appareils) et les reapplique a chaque ouverture de
// la meme liste, identifiee par le modele + l'ensemble des colonnes
// affichees. S'applique a toutes les listes de l'ERP (ListRenderer est le
// composant generique utilise partout).

const STORAGE_PREFIX = "aptytudes_col_widths:";

function getStorageKey(resModel, columns) {
    return STORAGE_PREFIX + resModel + ":" + columns.map((c) => c.name).join(",");
}

function readSavedWidths(key) {
    try {
        const raw = window.localStorage.getItem(key);
        return raw ? JSON.parse(raw) : null;
    } catch {
        return null;
    }
}

function writeSavedWidths(key, widths) {
    try {
        window.localStorage.setItem(key, JSON.stringify(widths));
    } catch {
        // localStorage indisponible/plein : on ignore silencieusement, la
        // memorisation n'est qu'un confort, pas une fonctionnalite critique.
    }
}

patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        if (!this.constructor.useMagicColumnWidths) {
            return;
        }

        // Reapplique les largeurs sauvegardees apres chaque calcul natif
        // (au montage, et a chaque fois que la table est recalculee : ajout
        // d'une ligne, filtre, etc.).
        useEffect(() => {
            const table = this.tableRef.el;
            if (!table || this.columnWidths.resizing) {
                return;
            }
            const key = getStorageKey(this.props.list.resModel, this.columns);
            const saved = readSavedWidths(key);
            if (!saved) {
                return;
            }
            const headers = [...table.querySelectorAll("thead th")];
            const offset = this.hasSelectors ? 1 : 0;
            for (let index = 0; index < this.columns.length; index++) {
                const width = saved[this.columns[index].name];
                const th = headers[index + offset];
                if (width && th) {
                    th.style.width = `${width}px`;
                }
            }
        });

        // Reprend le handler natif de redimensionnement pour sauvegarder les
        // largeurs finales une fois le glissement termine (relachement de
        // la souris), sans modifier son comportement natif.
        const originalOnStartResize = this.columnWidths.onStartResize;
        this.columnWidths.onStartResize = (ev) => {
            originalOnStartResize(ev);
            const onStop = () => {
                window.removeEventListener("pointerup", onStop);
                requestAnimationFrame(() => {
                    const table = this.tableRef.el;
                    if (!table) {
                        return;
                    }
                    const headers = [...table.querySelectorAll("thead th")];
                    const offset = this.hasSelectors ? 1 : 0;
                    const widths = {};
                    for (let index = 0; index < this.columns.length; index++) {
                        const th = headers[index + offset];
                        if (th) {
                            widths[this.columns[index].name] = Math.round(
                                th.getBoundingClientRect().width
                            );
                        }
                    }
                    const key = getStorageKey(this.props.list.resModel, this.columns);
                    writeSavedWidths(key, widths);
                });
            };
            window.addEventListener("pointerup", onStop);
        };
    },
});
