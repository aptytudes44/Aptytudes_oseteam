# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "Account"

    account_wording = fields.Selection([
        ('property', 'Property'),
        ('service', 'Service delivery')],
        string='Account wording', store=True)
