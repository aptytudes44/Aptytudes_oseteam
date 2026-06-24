# -*- coding: utf-8 -*-
from odoo import fields, models


class BaseDocumentLayout(models.TransientModel):
    _inherit = "base.document.layout"

    logo_iso = fields.Binary(related="company_id.logo_iso", readonly=False)
    logo_iso_text = fields.Char(related="company_id.logo_iso_text", readonly=False)
