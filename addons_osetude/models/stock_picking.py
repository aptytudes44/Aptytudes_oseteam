# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = "stock.picking"
    _description = "Transfer"

    def set_to_draft(self):
        move_lines = self.env['stock.move'].search([('picking_id', '=', self.id)])
        for move in move_lines:
            move.write({'state': 'draft'})

    def _compute_print_delivery_slip_ok(self):
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                precision_digits = self.env['decimal.precision'].precision_get(
                    'Product Unit of Measure')
                no_quantities_done = all(
                    float_is_zero(ml.qty_done, precision_digits=precision_digits)
                    for ml in picking.move_line_ids.filtered(
                        lambda m: m.state not in ('done', 'cancel')))
                picking.print_deliveryslip_ok = False
                full_delivery_slip = True
                if picking.state in ('done', 'cancel'):
                    picking.print_deliveryslip_ok = True
                    full_delivery_slip = False
                    no_quantities_done = False
                else:
                    for line in picking.move_ids:
                        if line.product_uom_qty != line.quantity_done:
                            full_delivery_slip = False
                            picking.print_deliveryslip_ok = True
                if full_delivery_slip or (no_quantities_done and not full_delivery_slip):
                    if picking.project_id:
                        checklist_ok = all(
                            line.checked for line in picking.project_id.checklist_line)
                        if (checklist_ok
                                and picking.project_id.date_verification
                                and picking.project_id.name_auditor):
                            picking.print_deliveryslip_ok = True
                        else:
                            picking.print_deliveryslip_ok = False
            else:
                picking.print_deliveryslip_ok = True

    def _compute_print_satisfaction_ok(self):
        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                picking.print_satisfaction_ok = False
                backorder = self.env['stock.picking'].search(
                    [('backorder_id', '=', picking.id)])
                if not backorder and picking.state == 'done':
                    picking.print_satisfaction_ok = True
            else:
                picking.print_satisfaction_ok = False

    def button_validate(self):
        if not self.print_deliveryslip_ok:
            raise UserError(
                _('You cannot validate a transfer if check-list is not OK !'))
        return super(Picking, self).button_validate()

    project_id = fields.Many2one('project.project', string="Project")
    delivery_note = fields.Char(string='Note')
    print_deliveryslip_ok = fields.Boolean(
        'Print deliveryslip ok ?', compute='_compute_print_delivery_slip_ok')
    print_satisfaction_ok = fields.Boolean(
        'Print satisfaction_ok ?', compute='_compute_print_satisfaction_ok')
