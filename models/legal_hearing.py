from odoo import models, fields


class LegalHearing(models.Model):
    _name = "legal.hearing"
    _description = "Legal Hearing"

    name = fields.Char(string="Hearing Reference", required=True)
    case_id = fields.Many2one(
        "legal.case", string="Case", required=True, ondelete="cascade"
    )
    date = fields.Date(string="Hearing Date")
    description = fields.Text(string="Notes")
