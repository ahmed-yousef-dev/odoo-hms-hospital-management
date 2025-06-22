# -*- coding: utf-8 -*-
"""
HMS Patient Model

This module defines the Patient model for the Hospital Management System.
It manages patient information, medical records, and department assignments.
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date
import re
from odoo import api, SUPERUSER_ID


class HmsPatient(models.Model):
    """
    Hospital Management System - Patient Model

    This model represents patients in the hospital with their personal information,
    medical records, department assignments, and state tracking.
    """

    _name = "hms.patient"
    _description = "HMS Patient"
    _order = "last_name, first_name"
    _rec_name = "display_name"

    # ========================================
    # PERSONAL INFORMATION FIELDS
    # ========================================

    first_name = fields.Char(
        string="First Name", required=True, help="Patient's first name"
    )

    last_name = fields.Char(
        string="Last Name", required=True, help="Patient's last name"
    )

    birth_date = fields.Date(
        string="Date of Birth",
        required=True,
        help="Patient's birth date (used to calculate age automatically)",
    )

    email = fields.Char(
        string="Email Address",
        required=True,
        help="Patient's email address (must be unique)",
    )

    image = fields.Binary(string="Patient Photo", help="Patient's profile picture")

    address = fields.Text(string="Home Address", help="Patient's residential address")

    # ========================================
    # MEDICAL INFORMATION FIELDS
    # ========================================

    history = fields.Html(
        string="Medical History",
        help="Patient's medical history (only visible for patients 50+ years old)",
    )

    cr_ratio = fields.Float(
        string="CR Ratio",
        digits=(5, 2),
        help="Creatinine Ratio - mandatory when PCR is checked",
    )

    blood_type = fields.Selection(
        selection=[
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
            ("O+", "O+"),
            ("O-", "O-"),
        ],
        string="Blood Type",
        help="Patient's blood type",
    )

    pcr = fields.Boolean(
        string="PCR Required",
        default=False,
        help="Indicates if PCR test is required (auto-checked for patients under 30)",
    )

    # ========================================
    # COMPUTED FIELDS
    # ========================================

    age = fields.Integer(
        string="Age ",
        compute="_compute_age",
        store=True,
        help="Patient's age calculated from birth date",
    )

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Full name with email for identification",
    )

    # ========================================
    # RELATIONSHIP FIELDS
    # ========================================

    department_id = fields.Many2one(
        comodel_name="hms.department",
        string="Department",
        help="Department where patient is assigned",
    )

    doctors_ids = fields.Many2many(
        comodel_name="hms.doctors",
        relation="hms_patient_doctor_rel",
        column1="patient_id",
        column2="doctor_id",
        string="Assigned Doctors",
        help="Doctors assigned to this patient",
    )

    # ========================================
    # STATUS AND TRACKING FIELDS
    # ========================================

    state = fields.Selection(
        selection=[
            ("undetermined", "Undetermined"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("serious", "Serious"),
        ],
        string="Medical State",
        default="undetermined",
        required=True,
        help="Current medical condition state of the patient",
    )

    log_history_ids = fields.One2many(
        comodel_name="hms.patient.log",
        inverse_name="patient_id",
        string="Activity Log",
        help="History of all changes and activities for this patient",
    )

    # ========================================
    # DEPARTMENT CAPACITY FIELD
    # ========================================

    capacity = fields.Integer(
        string="Department Capacity",
        compute="_compute_capacity",
        help="Maximum capacity of the assigned department",
    )

    # ========================================
    # COMPUTED FIELD METHODS
    # ========================================

    @api.depends("first_name", "last_name", "email")
    def _compute_display_name(self):
        """
        Compute display name combining first name, last name, and email.
        """
        for record in self:
            if record.first_name and record.last_name and record.email:
                record.display_name = (
                    f"{record.first_name} {record.last_name} ({record.email})"
                )
            elif record.first_name and record.last_name:
                record.display_name = f"{record.first_name} {record.last_name}"
            else:
                record.display_name = record.email or "Unnamed Patient"

    @api.depends("birth_date")
    def _compute_age(self):
        """
        Calculate patient's age based on birth date.
        """
        today = date.today()
        for record in self:
            if record.birth_date:
                birth_date = record.birth_date
                age = today.year - birth_date.year

                # Adjust age if birthday hasn't occurred this year
                if today.month < birth_date.month or (
                    today.month == birth_date.month and today.day < birth_date.day
                ):
                    age -= 1

                record.age = max(0, age)  # Ensure age is not negative
            else:
                record.age = 0

    @api.depends("department_id")
    def _compute_capacity(self):
        """
        Get the capacity of the assigned department.
        """
        for record in self:
            record.capacity = (
                record.department_id.capacity if record.department_id else 0
            )

    # ========================================
    # VALIDATION METHODS
    # ========================================

    @api.constrains("email")
    def _check_email_format(self):
        """
        Validate email address format.
        """
        for record in self:
            if record.email:
                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, record.email):
                    raise ValidationError(
                        f"Invalid email format: '{record.email}'. "
                        "Please enter a valid email address."
                    )

    @api.constrains("email")
    def _check_email_unique(self):
        """
        Ensure email address is unique across all patients.
        """
        for record in self:
            if record.email:
                duplicate_patient = self.search(
                    [("email", "=", record.email), ("id", "!=", record.id)], limit=1
                )

                if duplicate_patient:
                    raise ValidationError(
                        f"Email address '{record.email}' is already used by another patient: "
                        f"{duplicate_patient.first_name} {duplicate_patient.last_name}. "
                        "Please use a different email address."
                    )

    @api.constrains("birth_date")
    def _check_birth_date_valid(self):
        """
        Ensure birth date is not in the future.
        """
        today = date.today()
        for record in self:
            if record.birth_date and record.birth_date > today:
                raise ValidationError(
                    "Birth date cannot be in the future. "
                    f"Please enter a valid birth date before {today}."
                )

    @api.constrains("cr_ratio")
    def _check_cr_ratio_positive(self):
        """
        Ensure CR ratio is positive when provided.
        """
        for record in self:
            if record.cr_ratio and record.cr_ratio < 0:
                raise ValidationError("CR Ratio must be a positive number.")

    # ========================================
    # ONCHANGE METHODS
    # ========================================

    @api.onchange("department_id")
    def _onchange_department_id(self):
        """
        Handle department selection changes.
        """
        if self.department_id:
            # Check if department is open
            if not self.department_id.is_opened:
                raise ValidationError(
                    f"Cannot assign patient to department '{self.department_id.name}' "
                    "because it is currently closed."
                )

        # Clear doctor assignments when department changes
        self.doctors_ids = [(5, 0, 0)]  # Remove all doctor assignments

    @api.onchange("pcr", "cr_ratio")
    def _onchange_pcr(self):
        """
        Handle PCR field changes and validate CR ratio requirement.
        """
        if self.pcr and not self.cr_ratio:
            raise ValidationError(
                "CR Ratio is mandatory when PCR is required. "
                "Please enter a valid CR Ratio value."
            )

    @api.onchange("age")
    def _onchange_age(self):
        """
        Handle age-related automatic field updates.
        """
        if self.age:
            # Clear medical history for patients under 50
            if self.age < 50:
                self.history = False

            # Auto-check PCR for patients under 30
            if self.age < 30 and not self.pcr:
                self.pcr = True
                return {
                    "warning": {
                        "title": "PCR Automatically Enabled",
                        "message": "PCR has been automatically enabled because the patient is under 30 years old.",
                    }
                }

    # ========================================
    # OVERRIDE METHODS
    # ========================================

    def name_get(self):
        """
        Custom display name format for patient records.
        """
        result = []
        for record in self:
            name = f"{record.first_name} {record.last_name} ({record.email})"
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        """
        Override create method to log patient creation.
        """
        patient = super(HmsPatient, self).create(vals)

        # Create initial log entry
        initial_state = dict(self._fields["state"].selection).get(
            patient.state, patient.state
        )

        patient.env["hms.patient.log"].create(
            {
                "patient_id": patient.id,
                "description": f"Patient created with initial state: {initial_state}",
            }
        )

        return patient

    def write(self, vals):
        """
        Override write method to log state changes.
        """
        # Log state changes before updating
        for record in self:
            if "state" in vals and vals["state"] != record.state:
                old_state = dict(self._fields["state"].selection).get(
                    record.state, record.state
                )
                new_state = dict(self._fields["state"].selection).get(
                    vals["state"], vals["state"]
                )

                # Create log entry for state change
                record.env["hms.patient.log"].create(
                    {
                        "patient_id": record.id,
                        "description": f"State changed from {old_state} to {new_state}",
                    }
                )

        return super(HmsPatient, self).write(vals)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        if user.has_group("hms.group_hms_user") and not user.has_group(
            "hms.group_hms_manager"
        ):
            args = args + [("create_uid", "=", user.id)]
        return super()._search(args, offset=offset, limit=limit, order=order)

    # ========================================
    # UTILITY METHODS
    # ========================================

    def add_log_entry(self, description):
        """
        Add a custom log entry for the patient.

        Args:
            description (str): Description of the log entry

        Returns:
            bool: True if log entry was created successfully
        """
        self.ensure_one()

        if not description:
            raise ValidationError("Log description cannot be empty.")

        self.env["hms.patient.log"].create(
            {"patient_id": self.id, "description": description}
        )

        return True

    def get_medical_summary(self):
        """
        Get a summary of patient's medical information.

        Returns:
            dict: Dictionary containing medical summary
        """
        self.ensure_one()

        return {
            "name": f"{self.first_name} {self.last_name}",
            "age": self.age,
            "blood_type": self.blood_type,
            "state": self.state,
            "department": (
                self.department_id.name if self.department_id else "Not Assigned"
            ),
            "pcr_required": self.pcr,
            "cr_ratio": self.cr_ratio if self.pcr else None,
            "assigned_doctors": len(self.doctors_ids),
        }

    def print_patient_status_report(self):
        return self.env.ref("hms.action_report_hms_patient_status").report_action(self)
