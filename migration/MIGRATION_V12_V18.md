# Migration Odoo V12 → V18 — oseteam

## Contexte

oseteam utilise un module custom `addons_osetude` développé sous Odoo 12.
La migration vers Odoo 18 s'effectue via l'outil de migration officiel Odoo
(dump V12 restauré sur une instance V18), mais cet outil ne migre pas les
données custom ni ne corrige certaines incompatibilités de structure.

Ce script corrige ces écarts **après** la migration officielle.

---

## Prérequis avant de lancer le script

1. Le dump V12 de production a été restauré sur l'instance V18
2. Le module `addons_osetude` a été mis à jour :
   ```bash
   sudo docker exec oseteam_v18_odoo odoo --config=/etc/odoo/odoo.conf \
     -d oseteam -u addons_osetude --stop-after-init
   sudo docker restart oseteam_v18_odoo
   ```
3. La table `account_invoice` (V12) est encore présente en base — le script
   en a besoin pour récupérer les données custom

---

## Lancement

```bash
sudo bash /opt/odoo-vps/clients/oseteam_V18/addons/Aptytudes_oseteam/migration/migrate_v12_to_v18.sh
```

Le script est **idempotent** : il peut être relancé plusieurs fois sans risque,
il ne modifie que ce qui n'a pas encore été corrigé.

---

## Ce que fait le script — détail des 6 corrections

### 1. Images partenaires

**Problème :** En V12, les images des partenaires étaient stockées dans
`ir_attachment` avec `res_field = 'image'`, `'image_medium'` ou `'image_small'`.
En V18, ces champs ont été renommés.

**Correction :**
- `image` → `image_1920`
- `image_medium` → `image_512`
- `image_small` → `image_128`

---

### 2. Champs custom sur les factures

**Problème :** oseteam a ajouté 3 champs sur les factures V12 (`account_invoice`) :
- `project_id` — projet lié à la facture
- `company_bank_id` — banque de la société
- `picking_id` — bon de livraison associé

En V18, `account_invoice` et `account_move` ont été fusionnés en un seul modèle
`account.move`. La migration officielle ne copie pas les champs custom.

**Correction :** copie de ces 3 champs de `account_invoice` vers `account_move`
en utilisant la correspondance `account_invoice.move_id = account_move.id`
(attention : **pas** `account_invoice.id = account_move.id`, qui est faux).

---

### 3. Noms clients sur les factures (invoice_partner_display_name)

**Problème :** En V18, `invoice_partner_display_name` est un champ calculé et
stocké. Quand `res.partner.name` est vide (cas des contacts rattachés à une
société), Odoo met en fallback "Créé par: NomUtilisateur", ce qui apparaît
dans la liste des factures à la place du nom client.

**Correction en 2 passes :**
- Passe 1 : partenaires dont le `name` est NULL ou vide → remplacer par le
  nom de la société parente (`parent_id.name`)
- Passe 2 : partenaires dont le `name` contient "Adresse de facturation"
  (valeur générée automatiquement par Odoo V12) → même correction

---

### 4. display_type des lignes de contrepartie (payment_term)

**Problème :** En V18, chaque écriture de facture contient des lignes typées :
- `display_type = 'product'` pour les lignes de produits/services
- `display_type = 'tax'` pour les lignes de TVA
- `display_type = 'payment_term'` pour la ligne de contrepartie client/fournisseur
  (celle qui sera lettrée au moment du paiement)

Après migration V12→V18, les lignes de contrepartie ont un `display_type`
incorrect (`'product'` au lieu de `'payment_term'`), ce qui provoque l'erreur
"The entry is not balanced" au passage en brouillon.

**Correction :** Pour identifier les lignes de contrepartie, on se base sur
`account_invoice.account_id` (le compte tiers de la facture V12) : toute ligne
`account_move_line` dont le `account_id` correspond à `account_invoice.account_id`
pour la même facture reçoit `display_type = 'payment_term'`.

---

### 5. account_type des comptes auxiliaires clients/fournisseurs

**Problème :** oseteam utilise des **comptes auxiliaires par partenaire**
au lieu du compte générique 410000/400000. Ces comptes ont des codes comme
`CAIRBUS` (client Airbus), `FKIPP` (fournisseur Kipp), etc.

Ces comptes ont été importés en V18 avec `account_type = 'income'` ou
`'expense'`, alors qu'ils devraient être `'asset_receivable'` (clients) ou
`'liability_payable'` (fournisseurs).

En V18, le module comptabilité cherche une ligne avec
`account_type IN ('asset_receivable', 'liability_payable')` pour calculer
le montant restant à payer et permettre l'enregistrement d'un paiement.
Avec le mauvais type, Odoo affiche "il n'y a plus rien à payer" même sur
des factures non soldées.

**Correction :**
- Comptes utilisés comme compte tiers dans des factures clients → `asset_receivable`
- Comptes utilisés comme compte tiers dans des factures fournisseurs → `liability_payable`

---

### 6. Traductions françaises des champs custom (ir_model_fields)

**Problème :** En V18, les libellés des champs custom sont stockés dans
`ir_model_fields.field_description` au format **jsonb multilingue**.
L'import du fichier de traduction (`--i18n-import fr.po`) ne met pas à jour
ce jsonb pour les champs custom — ils restent en anglais dans l'interface.

**Correction :** injection directe du libellé `fr_FR` dans le jsonb pour
chaque champ custom de `addons_osetude` :

| Modèle | Champ | Libellé fr_FR |
|--------|-------|---------------|
| account.move | project_id | Projet |
| account.move | title_project | Référence affaire |
| account.move | company_bank_id | Banque société |
| account.move | picking_id | Bon de livraison |
| account.move.line | account_wording | Type compte |
| account.journal | is_factor | Est un factor |
| account.journal | factor_note | Factor |

---

## Workflow complet du jour J (migration production)

```
1. Restore dump V12 prod sur l'instance V18
   → voir procédure dans la mémoire projet (MEMORY.md)

2. Corriger web.base.url
   sudo docker exec oseteam_v18_db psql -U odoo -d oseteam \
     -c "UPDATE ir_config_parameter SET value='https://oseteam-v18.applylog.com' WHERE key='web.base.url';"

3. Mettre à jour le module addons_osetude
   sudo docker exec oseteam_v18_odoo odoo --config=/etc/odoo/odoo.conf \
     -d oseteam -u addons_osetude --stop-after-init

4. Lancer ce script de migration
   sudo bash migration/migrate_v12_to_v18.sh

5. Redémarrer Odoo
   sudo docker restart oseteam_v18_odoo
```

---

## Structure du repo

```
Aptytudes_oseteam/
├── addons_osetude/          ← module Odoo (déployé via symlink dans Docker)
│   ├── models/
│   ├── views/
│   ├── report/
│   └── ...
└── migration/               ← scripts de migration (ce dossier)
    ├── migrate_v12_to_v18.sh
    └── MIGRATION_V12_V18.md
```
