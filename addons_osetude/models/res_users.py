# -*- coding: utf-8 -*-
from odoo import models


class ResUsers(models.Model):
    _inherit = 'res.users'

    def action_get(self):
        # hr.action_get() bascule sur la fiche employé complète dès qu'un
        # employé est lié à l'utilisateur. On revient ici à la vue
        # "Préférences" simplifiée pour tout le monde.
        return self.sudo().env.ref('base.action_res_users_my').read()[0]
