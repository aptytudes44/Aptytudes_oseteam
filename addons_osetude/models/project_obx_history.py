# -*- coding: utf-8 -*-

from odoo import fields, models


class ProjectOBXHistory(models.Model):
    _name = "project.obx.history"
    _description = "Project OBX History"

    name = fields.Char("Project")
    customer = fields.Char('Customer')
    ref_customer = fields.Char('Reference')
    description = fields.Text('Description')
