/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Field } from "@web/views/fields/field";

// La classe native "o_field_empty" ne reflète l'état vide QUE hors édition
// (voir fieldVisualFeedback dans field.js : empty = inEdit ? empty && readonly : empty).
// En formulaire éditable normal (inEdit=true, readonly=false), elle vaut donc
// toujours false. On calcule ici l'état vide réel, sans cette restriction,
// pour pouvoir colorer les champs obligatoires uniquement quand ils sont vides.
patch(Field.prototype, {
    get classNames() {
        const classNames = super.classNames;
        if (classNames.o_required_modifier) {
            const { record, name } = this.props;
            classNames.o_required_empty =
                "isEmpty" in this.field ? this.field.isEmpty(record, name) : !record.data[name];
        }
        return classNames;
    },
});
