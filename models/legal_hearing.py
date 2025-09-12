# Copyright (C) 2025  Vaibhav K Joshi & Prithvi Hegde
from odoo import models, fields


class LegalHearing(models.Model):
    _name = "legal.hearing"
    _description = "Legal Hearing"

    name = fields.Char(string="Subject", required=True)
    case_id = fields.Many2one(
        "legal.case", string="Case", required=True, ondelete="cascade"
    )
    date_start = fields.Datetime(string="Start", required=True)
    date_end = fields.Datetime(string="End")
    location = fields.Char(string="Location")
    status = fields.Selection(
        [
            ("planned", "Planned"),
            ("held", "Held"),
            ("adjourned", "Adjourned"),
            ("cancelled", "Cancelled"),
        ],
        default="planned",
        required=True,
    )
    notes = fields.Text(string="Notes")
