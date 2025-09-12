# Copyright (C) 2025  Vaibhav K Joshi & Prithvi Hegde
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_lawyer = fields.Boolean(string="Lawyer")
    is_client = fields.Boolean(string="Client")
    bar_number = fields.Char(string="Bar Number")
