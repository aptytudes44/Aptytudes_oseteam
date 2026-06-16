# -*- coding: utf-8 -*-
from datetime import timedelta, date, datetime
import shutil
import os

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class ProjectDefaultTask(models.Model):
    _name = "project.default.task"
    _description = "Project Default Task"
    _order = 'sequence, id'

    name = fields.Char('Name', required=True)
    type_ressource = fields.Selection([
        ('etude', "Bureau d'etude"),
        ('atelier', "Atelier"),
        ('montage', "Montage"),
    ], string="Type ressource", default='etude')
    sequence = fields.Integer(string="Sequence", default=10)


class TaskHours(models.Model):
    _name = 'project.task.hours'
    _description = "Task Hours"
    _order = 'name'

    task_hours__id = fields.Many2one('project.task', string='Tasks', required=True,
                                     ondelete='cascade', index=True, copy=False)
    name = fields.Datetime('Task date')
    hours = fields.Float('Hours')


class Task(models.Model):
    _inherit = 'project.task'
    _description = "Task"

    def task_done(self):
        return self.write({'state': 'done'})

    def write(self, vals):
        for task in self:
            timesheet_ids = self.env['account.analytic.line'].search(
                [('task_id', '=', task.id)])
            if timesheet_ids:
                if vals.get('state') == 'remove':
                    vals['state'] = 'new'
                if vals.get('new'):
                    vals['state'] = 'in_progress'
            else:
                vals['state'] = 'new'
        return super(Task, self).write(vals)

    def _compute_display_name(self):
        # v17 : name_get() deprecated → _compute_display_name()
        for task in self:
            task.display_name = '%s%s' % (
                task.project_id.name and '[%s] ' % task.project_id.name or '',
                task.name)

    state = fields.Selection(
        selection_add=[
            ('new', 'New'),
            ('in_progress', 'In progress'),
            ('remove', 'Remove'),
            ('done', 'Done'),
        ],
        ondelete={
            'new': 'set default',
            'in_progress': 'set default',
            'remove': 'set default',
            'done': 'set default',
        },
        default='new',
    )
    type_task = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string="Type task", default='internal')
    type_ressource = fields.Selection([
        ('etude', "Bureau d'etude"),
        ('atelier', "Atelier"),
        ('montage', "Montage"),
    ], string="Type ressource", default='etude')


class Project(models.Model):
    _inherit = "project.project"
    _description = "Project"
    _order = 'name desc, id desc'

    def url_folder_project(self):
        path = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'path_url_project_folder')]).value
        return path

    def url_model_folder_project(self):
        path_model = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', 'path_url_model_folder')]).value
        return path_model

    def re_create_folder(self):
        url = self.url_folder_project()
        url_model = self.url_model_folder_project()
        date_val = self.create_date
        try:
            shutil.copytree(url_model, url + str(date_val.year) + '/' + self.name)
        except OSError as error:
            raise UserError(_("Directory %s can not be created %s") % (url, error))

    def create_folder(self, date_val, project):
        url = self.url_folder_project()
        url_model = self.url_model_folder_project()
        try:
            shutil.copytree(url_model, url + str(date_val.year) + '/' + project.name)
        except OSError as error:
            _logger.info("ERROR ########## %s - %s", url, error)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('project.project')
        results = super(Project, self).create(vals_list)
        default_tasks = self.env['project.default.task'].search([], order='sequence, id')
        for result in results:
            for task in default_tasks:
                self.env['project.task'].create({
                    'project_id': result.id,
                    'name': str(task.name),
                    'partner_id': result.partner_id.id,
                    'type_ressource': task.type_ressource,
                    'sequence': task.sequence,
                })
            self.create_folder(datetime.today(), result)
            self._create_automatic_checklist_data(result.id)
        return results

    def _create_automatic_checklist_data(self, project_id):
        data_ids = self.env['quality.control.quality.cheklist.data'].search(
            [('default_data', '=', True)])
        for data in data_ids:
            self.env['quality.control.quality.cheklist'].create({
                'project_id': project_id,
                'name': data.id,
            })

    def _compute_url_folder(self):
        for project in self:
            url = project.url_folder_project()
            project.url_folder = str(url) + str(project.name)

    def _compute_purchase_line_count(self):
        # v17 : account_analytic_id removed from purchase.order.line
        # → search via purchase.order header's account_analytic_id (custom field)
        for project in self:
            amount = 0.0
            purchase_lines = self.env['purchase.order.line'].search(
                [('order_id.account_analytic_id', '=', project.account_id.id)])
            for line in purchase_lines:
                if line.order_id.state in ('purchase', 'done'):
                    amount += line.price_subtotal
            project.purchase_lines_count = amount

    def action_view_purchase_line(self):
        purchase_lines = self.env['purchase.order.line'].search(
            [('order_id.account_analytic_id', '=', self.analytic_account_id.id)])
        ids = [l.id for l in purchase_lines if l.order_id.state in ('purchase', 'done')]
        if ids:
            return {
                'name': _("Purchase order line"),
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order.line',
                'view_mode': 'tree,form',
                'context': "{'search_default_groupby_product': 1}",
                'domain': [('id', 'in', ids)],
                'target': 'current',
            }

    def _compute_sales_order_count(self):
        for project in self:
            amount = 0.0
            orders = self.env['sale.order'].search(
                [('project_id', '=', project.id), ('state', 'in', ('sale', 'done'))])
            for order in orders:
                amount += order.amount_untaxed
            project.sale_orders_count = amount

    def _compute_sales_quotations_count(self):
        for project in self:
            amount = 0.0
            orders = self.env['sale.order'].search(
                [('project_id', '=', project.id), ('state', 'in', ('draft', 'sent'))])
            for order in orders:
                amount += order.amount_untaxed
            project.sale_quotations_count = amount

    def _compute_sale_orders_references(self):
        for project in self:
            references = ''
            orders = self.env['sale.order'].search(
                [('project_id', '=', project.id), ('state', 'in', ('sale', 'done'))])
            for order in orders:
                references += order.name + ' '
            project.sale_orders_references = references

    def action_view_sales_orders(self):
        orders_ids = self.env['sale.order'].search(
            [('project_id', '=', self.id), ('state', 'in', ('sale', 'done'))])
        action = self.env.ref('sale.action_orders').read()[0]
        action['context'] = {'default_project_id': self.id}
        action['domain'] = [('id', 'in', orders_ids.ids)]
        return action

    def action_view_quotations_orders(self):
        orders_ids = self.env['sale.order'].search(
            [('project_id', '=', self.id), ('state', 'in', ('draft', 'sent'))])
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        action['context'] = {'default_project_id': self.id}
        action['domain'] = [('id', 'in', orders_ids.ids)]
        return action

    def _compute_analytic_count(self):
        for project in self:
            project.account_analytic_count = 1

    def action_view_analytic(self):
        analytic = self.env['account.analytic.account'].search(
            [('id', '=', self.analytic_account_id.id)])
        ids = analytic.ids
        if ids:
            return {
                'name': _("Analytic Account"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.analytic.account',
                'view_mode': 'tree',
                'domain': [('id', 'in', ids)],
                'target': 'current',
            }

    def _compute_account_invoice_amount(self):
        for project in self:
            amount = 0.0
            # v16 : account.move → account.move, type → move_type
            invoices = self.env['account.move'].search([
                ('project_id', '=', project.id),
                ('state', '!=', 'cancel'),
                ('move_type', '=', 'out_invoice'),
            ])
            for invoice in invoices:
                amount += invoice.amount_untaxed
            project.total_invoiced = amount

    def action_view_invoices(self):
        invoices = self.env['account.move'].search([
            ('project_id', '=', self.id),
            ('state', '!=', 'cancel'),
            ('move_type', '=', 'out_invoice'),
        ])
        if invoices:
            return {
                'name': _("Accounts invoices"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', invoices.ids)],
                'target': 'current',
            }

    def create_checklist_data(self):
        data_ids = self.env['quality.control.quality.cheklist.data'].search(
            [('default_data', '=', True)])
        for data in data_ids:
            self.env['quality.control.quality.cheklist'].create({
                'project_id': self.id,
                'name': data.id,
            })

    @api.depends('task_ids')
    def _compute_first_date_task(self):
        for project in self:
            date_task = False
            for task in project.task_ids:
                if not date_task:
                    date_task = task.date_deadline
                else:
                    if task.date_deadline and task.date_deadline < date_task:
                        date_task = task.date_deadline
            project.first_date_task = date_task

    # --- Fields ---
    project_state = fields.Selection([
        ('open', 'Open'),
        ('close', 'Close'),
    ], 'State', default='open')
    buyer_id = fields.Many2one('res.partner', string="Buyer")
    phone_buyer = fields.Char(related='buyer_id.mobile', string="Phone buyer")
    mail_buyer = fields.Char(related='buyer_id.email', string="Mail buyer")
    responsible_business_id = fields.Many2one('res.partner', string="Responsible business")
    
    related_partner_id = fields.Many2one(related='partner_id')
    
    phone_responsible_business = fields.Char(
        related='responsible_business_id.mobile', string="Phone responsible")
    mail_responsible_business = fields.Char(
        related='responsible_business_id.email', string="Mail responsible")
    title_project = fields.Char('Business reference')
    note = fields.Html('Note on the project')
    response_date = fields.Date('Response date')
    customer_reference = fields.Char('Customer reference')
    tools_number = fields.Char('Tools number')
    url_folder = fields.Char('URL Folder', compute='_compute_url_folder')
    purchase_lines_count = fields.Float(
        compute='_compute_purchase_line_count', string="Purchase Lines Amount")
    sale_orders_count = fields.Float(
        compute='_compute_sales_order_count', string="Sale Orders Count")
    sale_quotations_count = fields.Float(
        compute='_compute_sales_quotations_count', string="Sale Quotations Count")
    sale_orders_references = fields.Text(
        compute='_compute_sale_orders_references', string='Sale orders references')
    account_analytic_count = fields.Integer(
        compute='_compute_analytic_count', string="Analytic Count")
    total_invoiced = fields.Float(
        compute='_compute_account_invoice_amount', string="Total invoiced")
    currency_id = fields.Many2one(
        related='company_id.currency_id', string="Currency")
    checklist_line = fields.One2many(
        'quality.control.quality.cheklist', 'project_id', string='Check List Lines')
    date_verification = fields.Date('Date of verification')
    name_auditor = fields.Many2one('res.users', string="Name of auditor")
    noncompliance_line = fields.One2many(
        'quality.control.quality.noncompliance', 'project_id', string='Noncompliance Lines')
    first_date_task = fields.Datetime(
        compute='_compute_first_date_task', store=True, string="First date task")
