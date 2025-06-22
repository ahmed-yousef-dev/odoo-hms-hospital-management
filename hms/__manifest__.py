{
    "name": "Hospital Management System",
    "version": "1.1",
    "category": "Healthcare",
    "summary": "Manage hospital patients",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "crm",
    ],
    "data": [
        "security/hms_groups.xml",
        "security/ir.model.access.csv",
        "views/hms_patient_view.xml",
        "views/res_partner_views.xml",
        # "views/assets.xml",
        "report/hms_patient_report.xml",
        "report/hms_patient_report_template.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hms/static/src/css/hms_patient.css",
        ],
    },
    "installable": True,
    "application": True,
}
