# -*- coding: utf-8 -*-
"""
HMS Doctors Model

This module defines the Doctors model for the Hospital Management System.
It manages doctor information and their assignments to patients.
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HmsDoctors(models.Model):
    """
    Hospital Management System - Doctors Model

    This model represents doctors in the hospital with their basic information
    and patient assignments.
    """

    _name = "hms.doctors"
    _description = "HMS Doctors"
    _order = "last_name, first_name"
    _rec_name = "display_name"

    # Personal Information
    first_name = fields.Char(
        string="First Name", required=True, help="Doctor's first name"
    )

    last_name = fields.Char(
        string="Last Name", required=True, help="Doctor's last name"
    )

    image = fields.Binary(string="Photo", help="Doctor's profile picture")

    # Professional Information
    specialization = fields.Char(
        string="Specialization", help="Doctor's medical specialization"
    )

    license_number = fields.Char(
        string="Medical License Number",
        help="Doctor's professional medical license number",
    )

    phone = fields.Char(string="Phone Number", help="Doctor's contact phone number")

    email = fields.Char(
        string="Email Address", help="Doctor's professional email address"
    )

    # Status and Availability
    is_active = fields.Boolean(
        string="Active",
        default=True,
        help="Indicates if the doctor is currently active in the system",
    )

    # Relationships
    patient_ids = fields.Many2many(
        comodel_name="hms.patient",
        relation="hms_patient_doctor_rel",
        column1="doctor_id",
        column2="patient_id",
        string="Assigned Patients",
        help="Patients assigned to this doctor",
    )

    # Computed Fields
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Full name of the doctor for display purposes",
    )

    patient_count = fields.Integer(
        string="Number of Patients",
        compute="_compute_patient_count",
        help="Total number of patients assigned to this doctor",
    )

    @api.depends("first_name", "last_name")
    def _compute_display_name(self):
        """
        Compute the full display name of the doctor.
        """
        for record in self:
            if record.first_name and record.last_name:
                record.display_name = f"Dr. {record.first_name} {record.last_name}"
            elif record.first_name:
                record.display_name = f"Dr. {record.first_name}"
            elif record.last_name:
                record.display_name = f"Dr. {record.last_name}"
            else:
                record.display_name = "Dr. [Name Missing]"

    @api.depends("patient_ids")
    def _compute_patient_count(self):
        """
        Compute the number of patients assigned to each doctor.
        """
        for record in self:
            record.patient_count = len(record.patient_ids)

    @api.constrains("email")
    def _check_email_format(self):
        """
        Validate email format if provided.
        """
        import re

        for record in self:
            if record.email:
                email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                if not re.match(email_pattern, record.email):
                    raise ValidationError(
                        f"Invalid email format for Dr. {record.first_name} {record.last_name}. "
                        "Please enter a valid email address."
                    )

    @api.constrains("phone")
    def _check_phone_format(self):
        """
        Validate phone number format if provided.
        """
        import re

        for record in self:
            if record.phone:
                # Allow various phone formats: +1234567890, (123) 456-7890, 123-456-7890, etc.
                phone_pattern = r"^[\+]?[\s\-\(\)0-9]{10,20}$"
                if not re.match(phone_pattern, record.phone):
                    raise ValidationError(
                        f"Invalid phone number format for Dr. {record.first_name} {record.last_name}. "
                        "Please enter a valid phone number."
                    )

    def name_get(self):
        """
        Custom display name with specialization if available.
        """
        result = []
        for record in self:
            name = f"Dr. {record.first_name} {record.last_name}"
            if record.specialization:
                name += f" ({record.specialization})"
            if not record.is_active:
                name += " [Inactive]"
            result.append((record.id, name))
        return result

    def toggle_active_status(self):
        """
        Toggle doctor's active status.
        """
        for record in self:
            record.is_active = not record.is_active
        return True
