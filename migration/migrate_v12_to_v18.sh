#!/bin/bash
# =============================================================================
# Migration données V12 → V18 — oseteam
# Rejouable à volonté après restore d'un dump V12
# Usage : sudo bash /home/ubuntu/migrate_v12_to_v18.sh
# =============================================================================

DB_CONTAINER="oseteam_v18_db"
DB_NAME="oseteam"
DB_USER="odoo"

run_sql() {
    local label="$1"
    local sql="$2"
    echo ""
    echo ">>> $label"
    result=$(sudo docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "$sql" 2>&1)
    echo "$result"
}

echo "============================================="
echo " Migration V12 → V18 oseteam"
echo " $(date)"
echo "============================================="

# -----------------------------------------------------------------------------
# 1. Images partenaires
#    En V12, ir_attachment utilisait image/image_medium/image_small
#    En V18, les champs sont image_1920/image_512/image_128
# -----------------------------------------------------------------------------
run_sql "Images partenaires — image → image_1920" \
"UPDATE ir_attachment SET res_field = 'image_1920'
 WHERE res_model = 'res.partner' AND res_field = 'image';"

run_sql "Images partenaires — image_medium → image_512" \
"UPDATE ir_attachment SET res_field = 'image_512'
 WHERE res_model = 'res.partner' AND res_field = 'image_medium';"

run_sql "Images partenaires — image_small → image_128" \
"UPDATE ir_attachment SET res_field = 'image_128'
 WHERE res_model = 'res.partner' AND res_field = 'image_small';"

# -----------------------------------------------------------------------------
# 2. Champs custom factures
#    En V12 : account_invoice. En V18 : account_move (fusionné).
#    La correspondance est ai.move_id = am.id (PAS ai.id = am.id !)
# -----------------------------------------------------------------------------
run_sql "Champs custom factures — project_id, company_bank_id, picking_id" \
"UPDATE account_move am
 SET project_id      = ai.project_id,
     company_bank_id = ai.company_bank_id,
     picking_id      = ai.picking_id
 FROM account_invoice ai
 WHERE am.id = ai.move_id
   AND (
     ai.project_id      IS NOT NULL OR
     ai.company_bank_id IS NOT NULL OR
     ai.picking_id      IS NOT NULL
   );"

# -----------------------------------------------------------------------------
# 3. invoice_partner_display_name
#    V18 calcule ce champ et le stocke. Quand partner.name est vide,
#    Odoo met "Créé par: X" en fallback. On corrige en 2 passes.
# -----------------------------------------------------------------------------
run_sql "invoice_partner_display_name — partenaires sans nom (→ nom parent)" \
"UPDATE account_move am
 SET invoice_partner_display_name = rp_parent.name
 FROM res_partner rp
 JOIN res_partner rp_parent ON rp_parent.id = rp.parent_id
 WHERE am.partner_id = rp.id
   AND (rp.name IS NULL OR rp.name = '')
   AND rp.parent_id IS NOT NULL
   AND rp_parent.name IS NOT NULL
   AND rp_parent.name != '';"

run_sql "invoice_partner_display_name — partenaires 'Adresse de facturation' (→ nom parent)" \
"UPDATE account_move am
 SET invoice_partner_display_name = rp_parent.name
 FROM res_partner rp
 JOIN res_partner rp_parent ON rp_parent.id = rp.parent_id
 WHERE am.partner_id = rp.id
   AND rp.name ILIKE 'adresse de facturation%'
   AND rp.parent_id IS NOT NULL
   AND rp_parent.name IS NOT NULL
   AND rp_parent.name != '';"

# -----------------------------------------------------------------------------
# 4. display_type des lignes de contrepartie
#    En V12, account_invoice.account_id pointait le compte client/fournisseur.
#    En V18, ces lignes doivent avoir display_type='payment_term' pour que
#    le module comptabilité les reconnaisse comme lignes de règlement.
# -----------------------------------------------------------------------------
run_sql "display_type payment_term — lignes de contrepartie factures" \
"UPDATE account_move_line aml
 SET display_type = 'payment_term'
 FROM account_invoice ai
 WHERE ai.move_id = aml.move_id
   AND ai.account_id = aml.account_id
   AND aml.display_type != 'payment_term';"

# -----------------------------------------------------------------------------
# 5. account_type des comptes auxiliaires clients/fournisseurs
#    Oseteam utilise des comptes par partenaire (CAIRBUS, FKIPP, etc.)
#    importés avec le mauvais account_type (income/expense).
#    V18 cherche asset_receivable/liability_payable pour enregistrer un paiement.
# -----------------------------------------------------------------------------
run_sql "account_type — comptes clients auxiliaires → asset_receivable" \
"UPDATE account_account aa
 SET account_type = 'asset_receivable'
 FROM (
   SELECT DISTINCT ai.account_id
   FROM account_invoice ai
   JOIN account_move am ON am.id = ai.move_id
   WHERE am.move_type IN ('out_invoice','out_refund')
 ) sub
 WHERE aa.id = sub.account_id
   AND aa.account_type != 'asset_receivable';"

run_sql "account_type — comptes fournisseurs auxiliaires → liability_payable" \
"UPDATE account_account aa
 SET account_type = 'liability_payable'
 FROM (
   SELECT DISTINCT ai.account_id
   FROM account_invoice ai
   JOIN account_move am ON am.id = ai.move_id
   WHERE am.move_type IN ('in_invoice','in_refund')
 ) sub
 WHERE aa.id = sub.account_id
   AND aa.account_type != 'liability_payable';"

# -----------------------------------------------------------------------------
# 6. Traductions champs custom (ir_model_fields.field_description jsonb)
#    En V18, les labels des champs custom sont dans le jsonb field_description.
#    --i18n-import ne les touche pas, il faut les mettre directement.
# -----------------------------------------------------------------------------
run_sql "Traductions — account.move.project_id" \
"UPDATE ir_model_fields SET field_description = field_description || '{\"fr_FR\": \"Projet\"}'::jsonb
 WHERE model = 'account.move' AND name = 'project_id'
   AND NOT (field_description ? 'fr_FR');"

run_sql "Traductions — account.move.title_project" \
"UPDATE ir_model_fields SET field_description = field_description || '{\"fr_FR\": \"Référence affaire\"}'::jsonb
 WHERE model = 'account.move' AND name = 'title_project'
   AND NOT (field_description ? 'fr_FR');"

run_sql "Traductions — account.move.company_bank_id" \
"UPDATE ir_model_fields SET field_description = field_description || '{\"fr_FR\": \"Banque société\"}'::jsonb
 WHERE model = 'account.move' AND name = 'company_bank_id'
   AND NOT (field_description ? 'fr_FR');"

run_sql "Traductions — account.move.picking_id" \
"UPDATE ir_model_fields SET field_description = field_description || '{\"fr_FR\": \"Bon de livraison\"}'::jsonb
 WHERE model = 'account.move' AND name = 'picking_id'
   AND NOT (field_description ? 'fr_FR');"

run_sql "Traductions — account.move.line.account_wording" \
"UPDATE ir_model_fields SET field_description = field_description || '{\"fr_FR\": \"Type compte\"}'::jsonb
 WHERE model = 'account.move.line' AND name = 'account_wording'
   AND NOT (field_description ? 'fr_FR');"

run_sql "Traductions — account.journal.is_factor" \
"UPDATE ir_model_fields SET field_description = field_description || '{\"fr_FR\": \"Est un factor\"}'::jsonb
 WHERE model = 'account.journal' AND name = 'is_factor'
   AND NOT (field_description ? 'fr_FR');"

run_sql "Traductions — account.journal.factor_note" \
"UPDATE ir_model_fields SET field_description = field_description || '{\"fr_FR\": \"Factor\"}'::jsonb
 WHERE model = 'account.journal' AND name = 'factor_note'
   AND NOT (field_description ? 'fr_FR');"

echo ""
echo "============================================="
echo " Migration terminée — $(date)"
echo "============================================="
