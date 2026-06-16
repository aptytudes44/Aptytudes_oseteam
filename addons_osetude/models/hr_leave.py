# -*- coding: utf-8 -*-
import logging
from collections import namedtuple
from datetime import datetime, time
from pytz import timezone, UTC

from odoo import api, fields, models
from odoo.tools.float_utils import float_to_time
from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period')


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"
    _description = "Leave"

    @api.onchange('request_date_from_period', 'request_hour_from', 'request_hour_to',
                  'request_date_from', 'request_date_to',
                  'employee_id', 'manual_hour_from', 'manual_hour_to')
    def _onchange_request_parameters(self):
        if not self.request_date_from:
            self.date_from = False
            return

        if self.request_unit_half or self.request_unit_hours:
            self.request_date_to = self.request_date_from

        if not self.request_date_to:
            self.date_to = False
            return

#        domain = [('calendar_id', '=',
#                   self.employee_id.resource_calendar_id.id
#                   or self.env.user.company_id.resource_calendar_id.id)]
                   
        attendances = self.env['resource.calendar.attendance'].read_group(
            domain,
            ['ids:array_agg(id)', 'hour_from:min(hour_from)',
             'hour_to:max(hour_to)', 'dayofweek', 'day_period'],
            ['dayofweek', 'day_period'],
            lazy=False,
        )
        attendances = sorted(
            [DummyAttendance(g['hour_from'], g['hour_to'], g['dayofweek'], g['day_period'])
             for g in attendances],
            key=lambda att: (att.dayofweek, att.day_period != 'morning'),
        )
        default_value = DummyAttendance(0, 0, 0, 'morning')

        attendance_from = next(
            (att for att in attendances
             if int(att.dayofweek) >= self.request_date_from.weekday()),
            attendances[0] if attendances else default_value)
        attendance_to = next(
            (att for att in reversed(attendances)
             if int(att.dayofweek) <= self.request_date_to.weekday()),
            attendances[-1] if attendances else default_value)

        if self.request_unit_half:
            if self.request_date_from_period == 'am':
                hour_from = float_to_time(attendance_from.hour_from)
                hour_to = float_to_time(attendance_from.hour_to)
            else:
                hour_from = float_to_time(attendance_to.hour_from)
                hour_to = float_to_time(attendance_to.hour_to)
        elif self.request_unit_hours:
            hour_from = float_to_time(
                abs(self.manual_hour_from) if self.manual_hour_from < 0
                else self.manual_hour_from)
            hour_to = float_to_time(
                abs(self.manual_hour_to) if self.manual_hour_to < 0
                else self.manual_hour_to)
        else:
            hour_from = float_to_time(attendance_from.hour_from)
            hour_to = float_to_time(attendance_to.hour_to)

        tz = self.env.user.tz if self.env.user.tz else 'UTC'
        self.date_from = (timezone(tz)
                          .localize(datetime.combine(self.request_date_from, hour_from))
                          .astimezone(UTC).replace(tzinfo=None))
        self.date_to = (timezone(tz)
                        .localize(datetime.combine(self.request_date_to, hour_to))
                        .astimezone(UTC).replace(tzinfo=None))
        self._onchange_leave_dates()

    manual_hour_from = fields.Float('From')
    manual_hour_to = fields.Float('To')
