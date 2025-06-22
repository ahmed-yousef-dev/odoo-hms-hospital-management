# -*- coding: utf-8 -*-
"""
HMS Patient Log Model

This module defines the Patient Log model for the Hospital Management System.
It tracks all activities and changes related to patients for audit purposes.
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HmsPatientLog(models.Model):
    """
    Hospital Management System - Patient Log Model

    This model maintains a comprehensive log of all patient-related activities,
    changes, and events for audit trail and historical tracking purposes.
    """

    _name = "hms.patient.log"
    _description = "HMS Patient Activity Log"
    _order = "date desc, id desc"
    _rec_name = "description"

    # ========================================
    # CORE FIELDS
    # ========================================

    patient_id = fields.Many2one(
        comodel_name="hms.patient",
        string="Patient",
        required=True,
        ondelete="cascade",
        help="Patient this log entry belongs to",
    )

    description = fields.Text(
        string="Activity Description",
        required=True,
        help="Detailed description of the activity or change",
    )

    date = fields.Datetime(
        string="Date & Time",
        default=fields.Datetime.now,
        required=True,
        help="When this activity occurred",
    )

    created_by = fields.Many2one(
        comodel_name="res.users",
        string="Created By",
        default=lambda self: self.env.user,
        required=True,
        help="User who created this log entry",
    )

    # ========================================
    # CATEGORIZATION FIELDS
    # ========================================

    log_type = fields.Selection(
        selection=[
            ("creation", "Patient Creation"),
            ("state_change", "State Change"),
            ("department_change", "Department Change"),
            ("doctor_assignment", "Doctor Assignment"),
            ("medical_update", "Medical Information Update"),
            ("system_note", "System Note"),
            ("manual_entry", "Manual Entry"),
        ],
        string="Log Type",
        default="manual_entry",
        required=True,
        help="Category of this log entry",
    )

    priority = fields.Selection(
        selection=[
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        string="Priority",
        default="normal",
        help="Priority level of this log entry",
    )

    # ========================================
    # COMPUTED FIELDS
    # ========================================

    patient_name = fields.Char(
        string="Patient Name",
        related="patient_id.display_name",
        store=True,
        help="Name of the patient for easy reference",
    )

    creator_name = fields.Char(
        string="Creator Name",
        related="created_by.name",
        store=True,
        help="Name of the user who created this log entry",
    )

    # ========================================
    # VALIDATION METHODS
    # ========================================

    @api.constrains("description")
    def _check_description_not_empty(self):
        """
        Ensure log description is not empty or just whitespace.
        """
        for record in self:
            if not record.description or not record.description.strip():
                raise ValidationError(
                    "Log description cannot be empty. "
                    "Please provide a meaningful description of the activity."
                )

    @api.constrains("date")
    def _check_date_not_future(self):
        """
        Ensure log date is not in the future.
        """
        now = fields.Datetime.now()
        for record in self:
            if record.date and record.date > now:
                raise ValidationError(
                    "Log date cannot be in the future. "
                    "Please use the current date and time or earlier."
                )

    # ========================================
    # OVERRIDE METHODS
    # ========================================

    def name_get(self):
        """
        Custom display name format for log entries.
        """
        result = []
        for record in self:
            # Format: "Patient Name - Date Time"
            patient_name = (
                f"{record.patient_id.first_name} {record.patient_id.last_name}"
            )
            formatted_date = record.date.strftime("%Y-%m-%d %H:%M")
            name = f"{patient_name} - {formatted_date}"
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        """
        Override create method to add automatic categorization.
        """
        # Auto-detect log type based on description keywords
        if "log_type" not in vals or vals["log_type"] == "manual_entry":
            description = vals.get("description", "").lower()

            if "created" in description and "initial state" in description:
                vals["log_type"] = "creation"
            elif "state changed" in description:
                vals["log_type"] = "state_change"
            elif "department" in description:
                vals["log_type"] = "department_change"
            elif "doctor" in description:
                vals["log_type"] = "doctor_assignment"
            elif any(
                keyword in description
                for keyword in ["medical", "pcr", "blood", "cr ratio"]
            ):
                vals["log_type"] = "medical_update"
            elif "system" in description or "automatic" in description:
                vals["log_type"] = "system_note"

        return super(HmsPatientLog, self).create(vals)

    # ========================================
    # UTILITY METHODS
    # ========================================

    @api.model
    def create_log_entry(
        self, patient_id, description, log_type="manual_entry", priority="normal"
    ):
        """
        Convenient method to create log entries programmatically.

        Args:
            patient_id (int): ID of the patient
            description (str): Description of the activity
            log_type (str): Type of log entry
            priority (str): Priority level

        Returns:
            recordset: Created log entry
        """
        if not patient_id or not description:
            raise ValidationError(
                "Patient ID and description are required to create a log entry."
            )

        return self.create(
            {
                "patient_id": patient_id,
                "description": description,
                "log_type": log_type,
                "priority": priority,
            }
        )

    def get_patient_activity_summary(self, patient_id, days=30):
        """
        Get a summary of patient activities for the last N days.

        Args:
            patient_id (int): ID of the patient
            days (int): Number of days to look back

        Returns:
            dict: Summary of activities
        """
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)

        logs = self.search(
            [("patient_id", "=", patient_id), ("date", ">=", start_date)]
        )

        summary = {
            "total_activities": len(logs),
            "by_type": {},
            "by_priority": {},
            "recent_activities": logs[:5].mapped("description"),
        }

        # Group by type
        for log in logs:
            log_type = log.log_type
            if log_type not in summary["by_type"]:
                summary["by_type"][log_type] = 0
            summary["by_type"][log_type] += 1

        # Group by
