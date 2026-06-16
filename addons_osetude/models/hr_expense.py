# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = "hr.expense"
    _description = "Expense"

    # In V17, tax_amount (company currency) is now a standard field (renamed from amount_tax_company).
    # We keep manual_tax_amount to allow overriding the tax amount manually.
    # The standard V17 tax_amount_currency field stores tax in invoice currency.
    manual_tax_amount = fields.Boolean("Manual Tax Amount")
