# -*- coding: utf-8 -*-
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SatisfactionSurveyParameters(models.Model):
    _name = "satisfaction.survey.parameters"
    _description = "Satisfaction survey parameters"

    @api.onchange('report_id')
    def _onchange_report_id(self):
        self.report_name = self.report_id.report_name

    report_id = fields.Many2one('ir.actions.report', string='Report Name')
    report_name = fields.Char(string='Report Model Name')
    satisfaction_survey_binary_model = fields.Binary('Satisfaction survey binary model')
    satisfaction_survey_binary_model_filename = fields.Char(
        'Satisfaction survey binary model filename')
    report_print_sequence = fields.Selection([
        ('before', 'Print before'),
        ('after', 'Print after'),
    ], required=True, default='after',
        help='Print the satisfaction survey before or after the document.')
