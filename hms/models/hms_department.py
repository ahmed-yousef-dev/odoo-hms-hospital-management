# -*- coding: utf-8 -*-
"""
HMS Department Model

This module defines the Department model for the Hospital Management System.
It manages hospital departments with their capacity and operational status.
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HmsDepartment(models.Model):
    """
    Hospital Management System - Department Model

    This model represents hospital departments with their basic information,
    capacity management, and patient assignments.
    """

    _name = "hms.department"
    _description = "HMS Department"
    _order = "name"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(
        string="Department Name", required=True, help="Name of the hospital department"
    )

    capacity = fields.Integer(
        string="Patient Capacity",
        default=0,
        help="Maximum number of patients this department can handle",
    )

    is_opened = fields.Boolean(
        string="Department Open",
        default=True,
        help="Indicates whether the department is currently operational",
    )

    # Relationships
    patients = fields.One2many(
        comodel_name="hms.patient",
        inverse_name="department_id",
        string="Assigned Patients",
        help="Patients currently assigned to this department",
    )

    # Computed Fields
    current_patient_count = fields.Integer(
        string="Current Patients",
        compute="_compute_current_patient_count",
        store=True,
        help="Number of patients currently in this department",
    )

    capacity_utilization = fields.Float(
        string="Capacity Utilization (%)",
        compute="_compute_capacity_utilization",
        help="Percentage of department capacity currently used",
    )

    @api.depends("patients")
    def _compute_current_patient_count(self):
        """
        Compute the current number of patients in the department.
        """
        for record in self:
            record.current_patient_count = len(record.patients)

    @api.depends("current_patient_count", "capacity")
    def _compute_capacity_utilization(self):
        """
        Calculate the capacity utilization percentage.
        """
        for record in self:
            if record.capacity > 0:
                record.capacity_utilization = (
                    record.current_patient_count / record.capacity
                ) * 100
            else:
                record.capacity_utilization = 0.0

    @api.constrains("capacity")
    def _check_capacity_positive(self):
        """
        Ensure department capacity is not negative.
        """
        for record in self:
            if record.capacity < 0:
                raise ValidationError("Department capacity cannot be negative!")

    @api.constrains("current_patient_count", "capacity")
    def _check_capacity_not_exceeded(self):
        """
        Prevent assigning more patients than department capacity allows.
        """
        for record in self:
            if record.capacity > 0 and record.current_patient_count > record.capacity:
                raise ValidationError(
                    f"Department '{record.name}' has reached its maximum capacity "
                    f"of {record.capacity} patients. "
                    f"Current patients: {record.current_patient_count}"
                )

    def name_get(self):
        """
        Custom display name showing department status and capacity info.
        """
        result = []
        for record in self:
            status = "Open" if record.is_opened else "Closed"
            name = f"{record.name} ({status} - {record.current_patient_count}/{record.capacity})"
            result.append((record.id, name))
        return result
