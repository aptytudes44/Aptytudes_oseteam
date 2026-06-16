# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _description = 'Analytic Line'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountAnalyticLine, self).create(vals_list)
        for record, vals in zip(records, vals_list):
            if vals.get('task_id'):
                task = self.env['project.task'].browse(vals['task_id'])
                if task and task.state == 'new':
                    task.write({'state': 'in_progress'})
        return records

    def unlink(self):
        for timesheet in self:
            task = self.env['project.task'].browse(timesheet.task_id.id)
            task.write({'state': 'remove'})
        return super(AccountAnalyticLine, self).unlink()

    name = fields.Char('Description', required=True, default='/')
