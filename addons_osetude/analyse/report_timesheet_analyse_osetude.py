# -*- coding: utf-8 -*-
# Migration v12→v16 :
# - Suppression # - get_object_reference → env.ref()
# - view_type supprimé des actions

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, timedelta

import logging
_logger = logging.getLogger(__name__)

WEEKEND = [5, 6]


class ReportResourcePlanningOsetudePeriode(models.TransientModel):
    _name = 'report.ressource.planning.osetude.periode'
    _description = 'Report Timesheet Analyse Osetude Periode'

    def _compute_num_week_total_data(self, NumWeek, Year, TypeRessource):
        TaskIds = self.env['project.task'].search([
            ('planned_hours', '>', 0.0),
            ('type_ressource', '=', TypeRessource),
            ('type_task', '=', 'internal'),
        ], order='date_start')
        AmountTotalHours = 0.0
        ListNbDayWeek = {}
        ListControl = []
        for Task in TaskIds:
            DateStart = DateEnd = False
            if Task.project_id.project_state == 'open' and Task.date_start:
                if Task.date_end and Task.date_end > Task.date_start:
                    DateStart = Task.date_start
                    DateEnd = Task.date_end
                else:
                    DateStart = DateEnd = Task.date_start
                NbTotalDays = 0
                for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1):
                    if date.fromordinal(d).weekday() not in WEEKEND:
                        NbTotalDays += 1
                if NbTotalDays == 0:
                    continue
                for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1):
                    NumWeekTask = date.fromordinal(d).isocalendar()[1]
                    YearTask = date.fromordinal(d).isocalendar()[0]
                    if date.fromordinal(d).weekday() not in WEEKEND:
                        if NumWeekTask == NumWeek and YearTask == Year:
                            if NumWeekTask not in ListControl:
                                ListControl.append(NumWeekTask)
                                ListNbDayWeek[NumWeekTask] = {
                                    'TotalAmountWeek': Task.planned_hours / NbTotalDays
                                }
                            else:
                                ListNbDayWeek[NumWeekTask]['TotalAmountWeek'] += (
                                    Task.planned_hours / NbTotalDays)
                try:
                    AmountTotalHours = ListNbDayWeek[NumWeek]['TotalAmountWeek']
                except Exception:
                    continue
        return AmountTotalHours

    def _compute_num_week_data(self, Project, NumWeek, Year):
        domain = [('project_id', '=', Project.id), ('planned_hours', '>', 0.0)]
        if self.type_ressource != 'toutes':
            domain.append(('type_ressource', '=', self.type_ressource))
        TaskIds = self.env['project.task'].search(domain, order='date_start')
        AmountHours = 0.0
        ListNbDayWeek = {}
        ListControl = []
        for Task in TaskIds:
            if Task.project_id.project_state == 'open' and Task.date_start:
                if Task.date_end and Task.date_end > Task.date_start:
                    DateStart, DateEnd = Task.date_start, Task.date_end
                else:
                    DateStart = DateEnd = Task.date_start
                NbTotalDays = sum(
                    1 for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1)
                    if date.fromordinal(d).weekday() not in WEEKEND)
                if NbTotalDays == 0:
                    continue
                NbDays = sum(
                    1 for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1)
                    if (date.fromordinal(d).weekday() not in WEEKEND
                        and date.fromordinal(d).isocalendar()[1] == NumWeek
                        and date.fromordinal(d).isocalendar()[0] == Year))
                for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1):
                    w = date.fromordinal(d).isocalendar()[1]
                    y = date.fromordinal(d).isocalendar()[0]
                    if date.fromordinal(d).weekday() not in WEEKEND and w == NumWeek and y == Year:
                        if w not in ListControl:
                            ListControl.append(w)
                            ListNbDayWeek[w] = {
                                'TotalAmountWeek': (Task.planned_hours / NbTotalDays) * NbDays
                            }
                        else:
                            ListNbDayWeek[w]['TotalAmountWeek'] = (
                                Task.planned_hours / NbTotalDays) * NbDays
            try:
                AmountHours += ListNbDayWeek[NumWeek]['TotalAmountWeek']
                ListNbDayWeek[NumWeek]['TotalAmountWeek'] = 0
            except Exception:
                continue
        return AmountHours

    def _compute_num_week(self):
        TaskIds = self.env['project.task'].search(
            [('planned_hours', '>', 0.0)], order='date_start')
        DateStart = DateEnd = False
        ListNumWeek = []
        ListControl = []
        for Task in TaskIds:
            if Task.project_id.project_state == 'open' and Task.date_start:
                if DateStart is False or DateStart > Task.date_start:
                    DateStart = Task.date_start
                if Task.date_end:
                    if DateEnd is False or DateEnd < Task.date_end:
                        DateEnd = Task.date_end
                else:
                    DateEnd = Task.date_start
        if DateStart is False:
            raise UserError(_(
                'Aucun projet à afficher sur le planning !\n'
                '- Pas de projets avec une commande de vente.\n'
                '- Pas de tâches avec des heures plannifiées.'))
        for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1):
            NumWeek = date.fromordinal(d).isocalendar()[1]
            Month = date.fromordinal(d).month
            Year = date.fromordinal(d).year
            if (NumWeek, Year) not in ListControl:
                if not (Month == 1 and NumWeek == 52):
                    ListControl.append((NumWeek, Year))
                    ListNumWeek.append((NumWeek, Month, Year))
        return ListNumWeek

    def _compute_num_week_day_data(self, Project, DateDay, Task):
        domain = [('id', '=', Task.id), ('project_id', '=', Project.id),
                  ('planned_hours', '>', 0.0)]
        if self.type_ressource != 'toutes':
            domain.append(('type_ressource', '=', self.type_ressource))
        TaskIds = self.env['project.task'].search(domain, order='date_start')
        AmountHours = 0.0
        for t in TaskIds:
            if t.project_id.project_state == 'open' and t.date_start:
                DateStart = t.date_start
                DateEnd = t.date_end if (t.date_end and t.date_end > t.date_start) else t.date_start
                TotalDays = sum(
                    1 for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1)
                    if date.fromordinal(d).weekday() not in WEEKEND)
                if TotalDays == 0:
                    continue
                for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1):
                    if (date.fromordinal(d).weekday() not in WEEKEND
                            and str(date.fromordinal(d)) == DateDay):
                        AmountHours += t.planned_hours / TotalDays
        return AmountHours

    def _compute_num_week_day_data_project(self, Project, DateDay):
        domain = [('project_id', '=', Project.id), ('planned_hours', '>', 0.0)]
        if self.type_ressource != 'toutes':
            domain.append(('type_ressource', '=', self.type_ressource))
        TaskIds = self.env['project.task'].search(domain, order='date_start')
        AmountHours = 0.0
        for t in TaskIds:
            if t.project_id.project_state == 'open' and t.date_start:
                DateStart = t.date_start
                DateEnd = t.date_end if (t.date_end and t.date_end > t.date_start) else t.date_start
                TotalDays = sum(
                    1 for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1)
                    if date.fromordinal(d).weekday() not in WEEKEND)
                if TotalDays == 0:
                    continue
                for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1):
                    if (date.fromordinal(d).weekday() not in WEEKEND
                            and str(date.fromordinal(d)) == DateDay):
                        AmountHours += t.planned_hours / TotalDays
        return AmountHours

    def _compute_num_week_days(self):
        TaskIds = self.env['project.task'].search(
            [('planned_hours', '>', 0.0)], order='date_start')
        DateStart = DateEnd = False
        ListNumWeekDays = {}
        ListControl = []
        for Task in TaskIds:
            if Task.project_id.project_state == 'open' and Task.date_start:
                if DateStart is False or DateStart > Task.date_start:
                    DateStart = Task.date_start
                if Task.date_end:
                    if DateEnd is False or DateEnd < Task.date_end:
                        DateEnd = Task.date_end
                else:
                    DateEnd = Task.date_start
        if DateStart is False:
            raise UserError(_(
                'Aucun projet à afficher sur le planning !\n'
                '- Pas de projets avec une commande de vente.\n'
                '- Pas de tâches avec des heures plannifiées.'))
        # Aligner sur début de semaine
        if date.fromordinal(DateStart.toordinal()).weekday() != 0:
            DateStart = DateStart + timedelta(
                days=-date.fromordinal(DateStart.toordinal()).weekday())
        if date.fromordinal(DateEnd.toordinal()).weekday() < 5:
            DateEnd = DateEnd + timedelta(
                days=(5 - date.fromordinal(DateEnd.toordinal()).weekday()))
        for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1):
            NumWeek = date.fromordinal(d).isocalendar()[1]
            Month = date.fromordinal(d).month
            Year = date.fromordinal(d).year
            Day = (date.fromordinal(d).strftime('%a').capitalize()
                   + ' ' + str(date.fromordinal(d).day)
                   + ' ' + date.fromordinal(d).strftime('%b').capitalize())
            FormatDate = date.fromordinal(d).strftime('%Y-%m-%d')
            if (NumWeek, Year) not in ListControl and date.fromordinal(d).weekday() not in WEEKEND:
                ListControl.append((NumWeek, Year))
                ListNumWeekDays[NumWeek] = {
                    'NumWeek': NumWeek, 'Month': Month, 'Year': Year,
                    'Days': [Day], 'FomatDate': [FormatDate],
                }
            elif date.fromordinal(d).weekday() not in WEEKEND:
                ListNumWeekDays[NumWeek]['Days'].append(Day)
                ListNumWeekDays[NumWeek]['FomatDate'].append(FormatDate)
        return ListNumWeekDays

    def _compute_num_week_data_task(self, Task, NumWeek, Year):
        domain = [('id', '=', Task.id), ('planned_hours', '>', 0.0)]
        if self.type_ressource != 'toutes':
            domain.append(('type_ressource', '=', self.type_ressource))
        TaskIds = self.env['project.task'].search(domain, order='date_start')
        AmountHours = 0.0
        ListNbDayWeek = {}
        ListControl = []
        for t in TaskIds:
            if t.project_id.project_state == 'open' and t.date_start:
                DateStart = t.date_start
                DateEnd = t.date_end if (t.date_end and t.date_end > t.date_start) else t.date_start
                NbTotalDays = sum(
                    1 for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1)
                    if date.fromordinal(d).weekday() not in WEEKEND)
                if NbTotalDays == 0:
                    continue
                NbDays = sum(
                    1 for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1)
                    if (date.fromordinal(d).weekday() not in WEEKEND
                        and date.fromordinal(d).isocalendar()[1] == NumWeek
                        and date.fromordinal(d).isocalendar()[0] == Year))
                for d in range(DateStart.toordinal(), DateEnd.toordinal() + 1):
                    w = date.fromordinal(d).isocalendar()[1]
                    y = date.fromordinal(d).isocalendar()[0]
                    if date.fromordinal(d).weekday() not in WEEKEND and w == NumWeek and y == Year:
                        if w not in ListControl:
                            ListControl.append(w)
                            ListNbDayWeek[w] = {
                                'TotalAmountWeek': (t.planned_hours / NbTotalDays) * NbDays
                            }
                        else:
                            ListNbDayWeek[w]['TotalAmountWeek'] = (
                                t.planned_hours / NbTotalDays) * NbDays
            try:
                AmountHours += ListNbDayWeek[NumWeek]['TotalAmountWeek']
                ListNbDayWeek[NumWeek]['TotalAmountWeek'] = 0
            except Exception:
                continue
        return AmountHours

    def compute_resource_planning(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env['ir.ui.menu'].sudo().search(
            [('name', '=', 'Projet'), ('complete_name', '=', 'Projet')])
        action_id = self.env['ir.actions.act_window'].search([
            ('name', '=', 'Projets'),
            ('target', '=', 'main'),
            ('res_model', '=', 'project.project'),
        ])

        ListeFilterTask = [dt.name for dt in self.type_task] if self.type_task else []

        if self.report_type == 'week':
            ProjectIdsSearch = self.env['project.project'].search(
                [('project_state', '=', 'open')], order='first_date_task')
            ProjectIds = [p for p in ProjectIdsSearch
                          if self.env['sale.order'].search([
                              ('project_id', '=', p.id),
                              ('state', 'not in', ('draft', 'sent', 'cancel'))])]

            ListNumWeek = self._compute_num_week()
            values = self._build_week_html(ProjectIds, ListNumWeek, ListeFilterTask,
                                           base_url, action_id, menu_id)

        elif self.report_type == 'weekdays':
            ProjectIdsSearch = self.env['project.project'].search(
                [('project_state', '=', 'open')], order='first_date_task')
            ProjectIds = [p for p in ProjectIdsSearch
                          if self.env['sale.order'].search([
                              ('project_id', '=', p.id),
                              ('state', 'not in', ('draft', 'sent', 'cancel'))])]
            ListNumWeekDays = self._compute_num_week_days()
            values = self._build_weekdays_html(ProjectIds, ListNumWeekDays, ListeFilterTask,
                                               base_url, action_id, menu_id)
        else:
            values = '<div>No data</div>'

        res = self.env['report.resource.planning.osetude'].create({'structure': values})
        # v16 : env.ref() remplace get_object_reference
        view_id = self.env.ref('addons_osetude.view_timesheet_analyse_osetude_form').id
        return {
            'name': _("Resource planning"),
            'type': 'ir.actions.act_window',
            'res_model': 'report.resource.planning.osetude',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_id': res.id,
            'context': {'no_breadcrumbs': True},
            'target': 'current',
        }

    def _build_week_html(self, ProjectIds, ListNumWeek, ListeFilterTask,
                         base_url, action_id, menu_id):
        """Génère le HTML du planning en mode semaine."""
        values = '<div class="oe_outer"><div class="oe_inner"><table class="oe_table">'
        values += ('<tr><td class="oe_title_analyse oe_fix">'
                   '<i class="fa fa-area-chart"/> Planning des ressources %s %s</td>'
                   % (self.env.user.company_id.name, date.today().year))
        for Week in ListNumWeek:
            cls = ('oe_table_analyse_week_today'
                   if date.today().isocalendar()[1] == Week[0]
                   else 'oe_table_analyse_week')
            values += ('<td class="%s"><span><i class="fa fa-calendar"/> '
                       'Semaine %s - %s</span></td>' % (cls, Week[0], Week[2]))
        values += '</tr>'

        for res_type, color, label in [
            ('etude', '#EDBB99', "Bureau d'études"),
            ('atelier', '#A9CCE3', "Atelier"),
            ('montage', '#ABEBC6', "Montage"),
        ]:
            if self.type_ressource in ('toutes', res_type):
                values += self._build_resource_row(
                    ListNumWeek, res_type, color, label)

        for Project in ProjectIds:
            domain = [('project_id', '=', Project.id), ('planned_hours', '>', 0.0)]
            if self.type_ressource != 'toutes':
                domain.append(('type_ressource', '=', self.type_ressource))
            if ListeFilterTask:
                domain.append(('name', 'in', ListeFilterTask))
            TaskIds = self.env['project.task'].search(domain)
            if not TaskIds:
                continue

            title = (Project.title_project[:60] + '...'
                     if Project.title_project and len(Project.title_project) > 60
                     else str(Project.title_project or ''))
            values += ('<tr><td class="oe_table_analyse_project oe_fix"><b>'
                       '<i class="fa fa-cubes"/>'
                       '<a href="%s/web#id=%s&model=project.project&view_type=form" '
                       'target="_blank">[%s]</a></b> '
                       '<span style="font-size:10px;font-style:italic;">%s</span></td>'
                       % (base_url, Project.id, Project.name, title))
            for Week in ListNumWeek:
                h = self._compute_num_week_data(Project, Week[0], Week[2])
                cls = 'oe_table_values_data' if h > 0 else 'oe_table_values_data_empty_project'
                values += '<td><div><div><table style="width:100%%"><tr>'
                values += '<td class="oe_table_values" style="background-color:#eae8e8;"></td>'
                values += '<td class="%s">%.2f h</td>' % (cls, h)
                values += '<td class="oe_table_values" style="background-color:#eae8e8;"></td>'
                values += '</tr></table></div></div></td>'
            values += '</tr>'

            for Task in TaskIds:
                cls_task = ('fa fa-tasks oe_type_task_external'
                            if Task.type_task == 'external'
                            else 'fa fa-tasks oe_type_task_internal')
                values += ('<tr><td class="oe_fix"><span class="oe_table_analyse_project_task">'
                           '<i class="%s"/> %s</span></td>' % (cls_task, Task.name))
                for Week in ListNumWeek:
                    v = self._compute_num_week_data_task(Task, Week[0], Week[2])
                    cls = ('oe_table_values_task oe_type_task_%s' % Task.type_task
                           if v > 0 else 'oe_table_values')
                    values += ('<td><div><div><table style="width:100%%"><tr>'
                               '<td class="oe_table_values_data_empty">0.0</td>'
                               '<td class="%s">%.2f h</td>'
                               '<td class="oe_table_values_data_empty">0.0</td>'
                               '</tr></table></div></div></td>' % (cls, v))
                values += '</tr>'

        values += '</table></div></div>'
        return values

    def _build_resource_row(self, ListNumWeek, res_type, color, label):
        """Génère une ligne de ressources pour le planning semaine."""
        values = ('<tr><td class="oe_table_legende_resource oe_fix">%s '
                  '<i class="fa fa-cogs fa-lg" style="color:%s;"/></td>' % (label, color))
        for Week in ListNumWeek:
            setting = self.env['report.resource.planning.osetude.setting.lines'].search(
                [('name', '=', Week[0]), ('year', '=', Week[2])], limit=1)
            if res_type == 'etude':
                resource = setting.amount2 if setting else 0.0
            elif res_type == 'atelier':
                resource = setting.amount if setting else 0.0
            else:
                resource = setting.amount3 if setting else 0.0
            total = self._compute_num_week_total_data(Week[0], Week[2], res_type)
            available = resource - total
            cls = ('oe_table_total_values_resource_%s' % res_type
                   if resource > 0 else 'oe_table_total_values_resource_alerte')
            values += ('<td><div><table style="width:100%%"><tr>'
                       '<td class="%s">%.2f h</td>'
                       '<td>%.2f h</td>'
                       '<td>%.2f h</td>'
                       '</tr></table></div></td>' % (cls, resource, total, available))
        values += '</tr>'
        return values

    def _build_weekdays_html(self, ProjectIds, ListNumWeekDays, ListeFilterTask,
                              base_url, action_id, menu_id):
        """Génère le HTML du planning en mode jours."""
        values = '<div class="oe_outer"><div class="oe_inner"><table class="oe_table">'
        values += ('<tr><td class="oe_title_analyse oe_fix">'
                   '<i class="fa fa-area-chart"/> Planning %s %s</td>'
                   % (self.env.user.company_id.name, date.today().year))
        for key, value in ListNumWeekDays.items():
            cls = ('oe_table_analyse_weekdays_today'
                   if date.today().isocalendar()[1] == key
                   else 'oe_table_analyse_weekdays')
            values += ('<td class="%s"><i class="fa fa-calendar"/> '
                       'Semaine %s - %s</td>' % (cls, value.get('NumWeek'), value.get('Year')))
        values += '</tr>'

        for Project in ProjectIds:
            domain = [('project_id', '=', Project.id), ('planned_hours', '>', 0.0)]
            if self.type_ressource != 'toutes':
                domain.append(('type_ressource', '=', self.type_ressource))
            if ListeFilterTask:
                domain.append(('name', 'in', ListeFilterTask))
            TaskIds = self.env['project.task'].search(domain)
            if not TaskIds:
                continue

            title = (Project.title_project[:75] + '...'
                     if Project.title_project and len(Project.title_project) > 75
                     else str(Project.title_project or ''))
            values += ('<tr><td class="oe_table_analyse_project oe_fix">'
                       '<b><i class="fa fa-cubes"/>'
                       '<a href="%s/web#id=%s&model=project.project&view_type=form" '
                       'target="_blank">[%s]</a></b> '
                       '<span style="font-size:10px;font-style:italic;">%s</span></td>'
                       % (base_url, Project.id, Project.name, title))
            for key, value in ListNumWeekDays.items():
                values += '<td><div><table style="width:100%%"><tr>'
                for DateDay in value.get('FomatDate', []):
                    h = self._compute_num_week_day_data_project(Project, DateDay)
                    cls = ('oe_table_values_data_days_project' if h > 0
                           else 'oe_table_values_data_empty_days_project')
                    values += '<td class="%s">%.2f h</td>' % (cls, h)
                values += '</tr></table></div></td>'
            values += '</tr>'

            for Task in TaskIds:
                cls_task = ('fa fa-tasks oe_type_task_%s' % Task.type_task)
                values += ('<tr><td class="oe_fix">'
                           '<span class="oe_table_analyse_project_task">'
                           '<i class="%s"/> %s</span></td>' % (cls_task, Task.name))
                for key, value in ListNumWeekDays.items():
                    values += '<td><div><table style="width:100%%"><tr>'
                    for DateDay in value.get('FomatDate', []):
                        h = self._compute_num_week_day_data(Project, DateDay, Task)
                        cls = ('oe_table_values_data_days oe_type_task_%s' % Task.type_task
                               if h > 0 else 'oe_table_values_data_empty_days')
                        values += '<td class="%s">%.2f h</td>' % (cls, h)
                    values += '</tr></table></div></td>'
                values += '</tr>'

        values += '</table></div></div>'
        return values

    # --- Fields ---
    date_start = fields.Date('Date start')
    date_end = fields.Date('Date end')
    report_type = fields.Selection([
        ('week', 'Week'),
        ('weekdays', 'Week Days'),
    ], string="Report Type", default='week')
    type_ressource = fields.Selection([
        ('toutes', 'Toutes'),
        ('etude', "Bureau d'etude"),
        ('atelier', "Atelier"),
        ('montage', "Montage"),
    ], string="Type ressource", default='toutes')
    type_task = fields.Many2many(
        'project.default.task', 'project_default_task_rel',
        'report_ressource_planning_id', 'project_default_task_id',
        string='Show tasks')


class ReportResourcePlanningOsetude(models.TransientModel):
    _name = 'report.resource.planning.osetude'
    _description = 'Report Resource Planning Osetude'

    name = fields.Char('Name', default='Resource planning')
    structure = fields.Html('Structure', readonly=True)


class ReportResourcePlanningOsetudeSetting(models.Model):
    _name = 'report.resource.planning.osetude.setting'
    _description = 'Report Resource Planning Osetude Setting'

    def create_period(self):
        ListNumWeek = []
        ListControl = []
        for d in range(self.date_start.toordinal(), self.date_end.toordinal() + 1):
            NumWeek = date.fromordinal(d).isocalendar()[1]
            Year = self.date_start.year
            if NumWeek not in ListControl:
                ListControl.append(NumWeek)
                ListNumWeek.append((NumWeek, Year))
        for Week in ListNumWeek:
            self.env['report.resource.planning.osetude.setting.lines'].create({
                'resource_planning_id': self.id,
                'name': Week[0],
                'year': Week[1],
                'amount': self.default_hours_atelier,
                'amount2': self.default_hours_etude,
                'amount3': self.default_hours_montage,
            })

    @api.depends('date_start', 'date_end')
    def _compute_period_name(self):
        for line in self:
            if line.date_start and line.date_end:
                line.name = (line.date_start.strftime("%d/%m/%Y")
                             + ' - ' + line.date_end.strftime("%d/%m/%Y"))

    name = fields.Char('Period', compute='_compute_period_name')
    date_start = fields.Date('Date start')
    date_end = fields.Date('Date end')
    default_hours_atelier = fields.Float('Heures atelier')
    default_hours_etude = fields.Float('Heures etude')
    default_hours_montage = fields.Float('Heures Montage')
    setting_line = fields.One2many(
        'report.resource.planning.osetude.setting.lines',
        'resource_planning_id', string='Setting Lines')


class ReportResourcePlanningOsetudeSettingLines(models.Model):
    _name = 'report.resource.planning.osetude.setting.lines'
    _description = 'Report Resource Planning Osetude Setting Lines'

    resource_planning_id = fields.Many2one(
        'report.resource.planning.osetude.setting',
        string='Resource Planning', required=True,
        ondelete='cascade', index=True, copy=False)
    name = fields.Integer('Week')
    year = fields.Integer('Year')
    amount = fields.Float('Atelier')
    amount2 = fields.Float('Etude')
    amount3 = fields.Float('Montage')
