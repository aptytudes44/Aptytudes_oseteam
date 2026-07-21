# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    logo_iso = fields.Binary(string="Logo ISO", attachment=True)
    logo_iso_text = fields.Char(string="Texte")
