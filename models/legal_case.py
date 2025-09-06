from odoo import models, fields


class LegalCase(models.Model):
    _name = "legal.case"
    _description = "Legal Case"

    name = fields.Char(string="Case Reference", required=True)
    client_id = fields.Many2one("res.partner", string="Client")
    lawyer_id = fields.Many2one("res.partner", string="Lawyer")
    responsible_lawyer_id = fields.Many2one("res.partner", string="Responsible Lawyer")
    date_open = fields.Date(string="Date Opened")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("closed", "Closed"),
        ],
        string="Status",
        default="draft",
    )
    stage = fields.Selection(
        [
            ("preparation", "Preparation"),
            ("hearing", "Hearing"),
            ("judgement", "Judgement"),
        ],
        string="Stage",
        default="preparation",
    )
    hearing_ids = fields.One2many("legal.hearing", "case_id", string="Hearings")
