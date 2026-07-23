# -*- coding: utf-8 -*-
# Migration v12→v16 :
#   - render_qweb_pdf → _render_qweb_pdf
#   - PyPDF2 3.x : PdfFileWriter→PdfWriter, PdfFileReader→PdfReader
#   - distutils supprimé

import base64
import io
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PdfReader
    except ImportError:
        # PyPDF2 < 3.0
        from PyPDF2 import PdfFileWriter as PdfWriter, PdfFileReader as PdfReader


class IrActionsReport(models.Model):
    _description = 'Report Action'
    _inherit = 'ir.actions.report'

    def _build_wkhtmltopdf_args(self, paperformat_id, landscape, specific_paperformat_args=None, set_viewport_size=False):
        # Certains rapports (ex: addons_osetude.report_project) n'utilisent pas le wrapper
        # standard <div class="article"> : le HTML transmis à wkhtmltopdf n'a alors ni
        # <head> ni <meta charset>, et wkhtmltopdf devine mal l'encodage (mojibake sur les
        # caractères accentués). On force donc explicitement l'UTF-8 en ligne de commande.
        command_args = super()._build_wkhtmltopdf_args(
            paperformat_id, landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )
        command_args.extend(['--encoding', 'utf-8'])
        return command_args

    # v16 : render_qweb_pdf → _render_qweb_pdf
    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        res = super(IrActionsReport, self)._render_qweb_pdf(report_ref, res_ids, data)
        pdf_content = res[0]

        report = self._get_report(report_ref)
        if not report:
            return res

        Model = self.env[report.model]
        record_ids = Model.browse(res_ids)

        if report.report_name == 'stock.report_deliveryslip':
            if (hasattr(record_ids, 'print_satisfaction_ok')
                    and record_ids.print_satisfaction_ok
                    and hasattr(record_ids, 'print_deliveryslip_ok')
                    and record_ids.print_deliveryslip_ok):
                survey_params = self.env['satisfaction.survey.parameters'].search(
                    [('report_name', '=', report.report_name)])
                if survey_params and survey_params.satisfaction_survey_binary_model:
                    pdf_data = []
                    survey_pdf = base64.b64decode(
                        survey_params.satisfaction_survey_binary_model)
                    if survey_params.report_print_sequence == 'after':
                        pdf_data = [res[0], survey_pdf]
                    else:
                        pdf_data = [survey_pdf, res[0]]

                    writer = PdfWriter()
                    for document in pdf_data:
                        reader = PdfReader(io.BytesIO(document), strict=False)
                        for page in reader.pages:
                            writer.add_page(page)
                    buffer = io.BytesIO()
                    writer.write(buffer)
                    pdf_content = buffer.getvalue()
                    buffer.close()

        return pdf_content, 'pdf'
