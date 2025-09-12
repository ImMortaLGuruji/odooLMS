# Copyright (C) 2025  Vaibhav K Joshi & Prithvi Hegde
{
    "name": "Legal Case Management",
    "version": "18.0.1.0.0",
    "category": "Services/Legal",
    "license": "AGPL-3",
    "summary": "Manage legal cases, hearings, documents, and fixed-fee invoicing",
    "author": "Vaibhav K Joshi, Prithvi Hegde, OCA",
    "website": "https://github.com/ImMortaLGuruji/odooLMS",
    "depends": ["base", "mail", "account", "calendar"],
    "data": [
        "security/legal_security.xml",
        "security/ir.model.access.csv",
        "data/legal_sequence.xml",
        "data/legal_menus.xml",
        "views/res_partner_views.xml",
        "views/legal_hearing_views.xml",
        "report/legal_case_report.xml",
        "views/legal_case_views.xml",
    ],
    "qweb": [
        "report/legal_case_template.xml",
    ],
    "demo": ["data/demo.xml"],
    "installable": True,
    "application": True,
}
