# -*- coding: utf-8 -*-
# Migration v12→v16 : account.move → account.move

from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def register_as_main_attachment(self, force=True):
        # Prevent account.move._sync_dynamic_lines from corrupting balance
        # when writing non-financial field message_main_attachment_id.
        return super(IrAttachment, self.with_context(skip_invoice_sync=True)).register_as_main_attachment(force=force)


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Invoice"

    @api.onchange('partner_id')
    def _onchange_partner_bank(self):
        self.company_bank_id = self.partner_id.company_bank_id.id

    project_id = fields.Many2one('project.project', string="Project")
    title_project = fields.Char(related="project_id.title_project", string='Business reference')
    company_bank_id = fields.Many2one('account.journal', string="Company Bank",
                                      domain=[('type', '=', 'bank')])
    picking_id = fields.Many2one('stock.picking', string="Picking Out",
                                 domain=[('picking_type_code', '=', 'outgoing')])


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _description = "Invoice Line"

    account_wording = fields.Selection(
        related='account_id.account_wording',
        string="wording account",
        store=True,
        readonly=True,
    )

    # Champ non stocke, utilise uniquement par le PDF (invoice_report_template.xml) :
    # retire le nom du produit en tete de la description quand elle est encore auto-
    # generee ("Etudes\n...", "Usinage\n..."), sans jamais modifier le champ `name`
    # reel (celui vu et modifie a l'ecran). Lignes personnalisees a la main inchangees.
    print_name = fields.Text(compute='_compute_print_name')

    @api.depends('name', 'product_id', 'display_type')
    def _compute_print_name(self):
        for line in self:
            name = line.name
            if line.display_type == 'product' and line.product_id and name:
                product_name = line.product_id.display_name
                if name != product_name:
                    if name.startswith(product_name + '\n'):
                        name = name[len(product_name) + 1:]
                    elif name.startswith(product_name + ' '):
                        name = name[len(product_name) + 1:]
            line.print_name = name


class AccountJournal(models.Model):
    _inherit = "account.journal"
    _description = "Journal"

    is_factor = fields.Boolean('Is factor')
    factor_note = fields.Html('Factor')
