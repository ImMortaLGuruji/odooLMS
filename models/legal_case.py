# Copyright (C) 2025  Vaibhav K Joshi & Prithvi Hegde
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LegalCase(models.Model):
    _name = "legal.case"
    _description = "Legal Case"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    # Identity & basic info
    name = fields.Char(
        string="Case Reference",
        required=True,
        copy=False,
        readonly=True,
        default="New",
        tracking=True,
    )
    description = fields.Text(string="Description")

    # Parties
    client_id = fields.Many2one(
        "res.partner",
        string="Client",
        required=True,
        domain=[("is_client", "=", True)],
        tracking=True,
    )
    responsible_lawyer_id = fields.Many2one(
        "res.partner",
        string="Responsible Lawyer",
        required=True,
        domain=[("is_lawyer", "=", True)],
        tracking=True,
    )
    # Helper to filter by the current user as responsible (maps lawyer partner -> user)
    responsible_user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        compute="_compute_responsible_user_id",
        store=True,
        index=True,
        help="Technical field mapping the responsible lawyer's partner to the corresponding user."
    )
    member_ids = fields.Many2many(
        "res.users",
        string="Team Members",
        help="Users who can access this case in addition to the responsible lawyer.",
    )

    # Classification
    case_type = fields.Selection(
        [
            ("civil", "Civil"),
            ("criminal", "Criminal"),
            ("corporate", "Corporate"),
            ("other", "Other"),
        ],
        string="Case Type",
        default="civil",
        required=True,
    )

    # Lifecycle
    stage = fields.Selection(
        [
            ("intake", "Intake"),
            ("active", "Active"),
            ("closed", "Closed"),
        ],
        string="Stage",
        default="intake",
        tracking=True,
    )
    open_date = fields.Date(
        string="Open Date",
        default=fields.Date.context_today,
        readonly=True,
        tracking=True,
    )
    close_date = fields.Date(string="Close Date", readonly=True, tracking=True)

    # Company & currency
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", store=True, readonly=True
    )

    # Billing
    fixed_fee_amount = fields.Monetary(
        string="Fixed Fee Amount", currency_field="currency_id"
    )
    invoice_ids = fields.One2many("account.move", "legal_case_id", string="Invoices")

    # Relations
    hearing_ids = fields.One2many("legal.hearing", "case_id", string="Hearings")

    # Smart counts
    hearing_count = fields.Integer(compute="_compute_counts")
    invoice_count = fields.Integer(compute="_compute_counts")

    @api.depends("hearing_ids", "invoice_ids")
    def _compute_counts(self):
        for rec in self:
            rec.hearing_count = len(rec.hearing_ids)
            rec.invoice_count = len(rec.invoice_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("legal.case") or _(
                    "New"
                )
            if not vals.get("open_date"):
                vals["open_date"] = fields.Date.context_today(self)
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "stage" in vals and vals.get("stage") == "closed":
            for rec in self:
                if not rec.close_date:
                    rec.close_date = fields.Date.context_today(self)
        return res

    @api.depends("responsible_lawyer_id")
    def _compute_responsible_user_id(self):
        # Batch map partners to users
        partners = self.mapped("responsible_lawyer_id")
        mapping = {}
        if partners:
            users = self.env["res.users"].search([("partner_id", "in", partners.ids)])
            mapping = {u.partner_id.id: u.id for u in users}
        for rec in self:
            rec.responsible_user_id = mapping.get(rec.responsible_lawyer_id.id)

    # Smart button actions
    def action_view_hearings(self):
        self.ensure_one()
        action = self.env.ref("legal_case_mgmt.action_legal_hearing").read()[0]
        action["domain"] = [("case_id", "=", self.id)]
        action["context"] = {
            "default_case_id": self.id,
        }
        return action

    def action_view_invoices(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": _("Invoices"),
            "res_model": "account.move",
            "view_mode": "list,form",
            "domain": [("legal_case_id", "=", self.id)],
            "context": {
                "default_legal_case_id": self.id,
                "default_move_type": "out_invoice",
            },
        }
        return action

    def action_view_attachments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documents"),
            "res_model": "ir.attachment",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }

    def action_create_invoice(self):
        self.ensure_one()
        if not self.fixed_fee_amount:
            raise UserError(
                _("Please set a Fixed Fee Amount before creating an invoice.")
            )

        # One invoice per case (ignore cancelled)
        existing = self.invoice_ids.filtered(
            lambda m: m.move_type == "out_invoice" and m.state != "cancel"
        )
        if existing:
            raise UserError(_("An invoice already exists for this case."))

        # Find or create a Legal Services product (service)
        product = self.env["product.product"].search(
            [("default_code", "=", "LEGAL_SERV")], limit=1
        )
        if not product:
            # Try to reuse an existing 'Legal Services' template if present
            tmpl = self.env["product.template"].search(
                [("name", "=", "Legal Services")], limit=1
            )
            if not tmpl:
                tmpl = self.env["product.template"].create(
                    {
                        "name": "Legal Services",
                        "type": "service",
                    }
                )
            # Use the auto-created single variant and set its default_code
            product = tmpl.product_variant_id
            if product and not product.default_code:
                product.default_code = "LEGAL_SERV"

        move_vals = {
            "move_type": "out_invoice",
            "partner_id": self.client_id.id,
            "invoice_origin": self.name,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "product_id": product.id,
                        "name": _("Legal Services - %s") % self.name,
                        "quantity": 1.0,
                        "price_unit": self.fixed_fee_amount,
                    },
                )
            ],
            "legal_case_id": self.id,
            "company_id": self.company_id.id,
        }
        move = self.env["account.move"].create(move_vals)
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
        }

    def action_print_case_summary(self):
        self.ensure_one()
        Report = self.env["ir.actions.report"]
        # 1) Try by XMLID
        try:
            report = self.env.ref("legal_case_mgmt.report_legal_case_summary")
            return report.report_action(self)
        except ValueError:
            pass

        # 2) Try by internal report name via API (safer than plain search)
        report = Report._get_report_from_name(
            "legal_case_mgmt.report_legal_case_summary_template"
        )
        if report:
            return report.report_action(self)

        # 3) Create the report action if missing (last resort)
        report = Report.create(
            {
                "name": "Case Summary",
                "model": "legal.case",
                "report_type": "qweb-pdf",
                "report_name": "legal_case_mgmt.report_legal_case_summary_template",
                "print_report_name": "'Case Summary - %s' % (object.name)",
            }
        )
        return report.report_action(self)
