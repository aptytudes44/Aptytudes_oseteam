/** @odoo-module **/

import { registry } from "@web/core/registry";
import { preferencesItem } from "@web/webclient/user_menu/user_menu_items";

// Le module "hr" remplace l'entrée "Préférences" par "Mon profil" (voir
// hr/static/src/user_menu/my_profile.js). On revient au libellé et au
// comportement standard ici, sans désinstaller hr.
registry.category("user_menuitems").add("profile", preferencesItem, { force: true });
