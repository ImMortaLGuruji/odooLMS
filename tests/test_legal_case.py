# Copyright (C) 2025  Vaibhav K Joshi & Prithvi Hegde
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLegalCase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Partner = self.env["res.partner"]
        self.Case = self.env["legal.case"]
        self.Hearing = self.env["legal.hearing"]

        self.client = self.Partner.create({"name": "Client A", "is_client": True})
        self.lawyer = self.Partner.create({"name": "Lawyer A", "is_lawyer": True})

    def test_case_flow_and_invoice(self):
        case = self.Case.create(
            {
                "client_id": self.client.id,
                "responsible_lawyer_id": self.lawyer.id,
                "case_type": "civil",
                "fixed_fee_amount": 100,
            }
        )

        self.assertTrue(case.name.startswith("CASE/"))
        self.assertEqual(case.stage, "intake")

        # Hearing
        self.Hearing.create(
            {
                "name": "Prelim",
                "case_id": case.id,
                "date_start": "2025-09-10 09:00:00",
            }
        )
        self.assertEqual(case.hearing_count, 1)

        # Invoice
        action = case.action_create_invoice()
        self.assertEqual(action["res_model"], "account.move")
        inv = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(inv.legal_case_id, case)

        # Report
    report = self.env.ref("legal_case_mgmt.report_legal_case_summary")
    html = report._render_qweb_html(case.ids)[0]
    self.assertTrue(html)
