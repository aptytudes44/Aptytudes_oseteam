# -*- coding: utf-8 -*-
# Migration v12→v16 :
# La méthode _create_invoice de sale.advance.payment.inv a été refactorisée en v14+
# En v16, on surcharge _create_invoices pour injecter project_id et company_bank_id

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    def _create_invoices(self, sale_orders):
        invoices = super(SaleAdvancePaymentInv, self)._create_invoices(sale_orders)
        for invoice in invoices:
            # Retrouver la commande correspondante
            order = sale_orders.filtered(
                lambda o: o.partner_id == invoice.partner_id
            )[:1]
            if order:
                invoice.write({
                    'project_id': order.project_id.id,
                    'company_bank_id': order.partner_id.company_bank_id.id,
                })
        return invoices
