from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Link customer with patient
    related_patient_id = fields.Many2one(
        "hms.patient",
        string="Related Patient",
        help="Link this customer to a patient in the HMS system",
    )

    # Make Tax ID mandatory for customers
    vat = fields.Char(required=True, help="Tax ID is mandatory for all customers")

    @api.constrains("related_patient_id", "email")
    def _check_patient_email_constraints(self):
        """Check all email-related constraints when patient is linked"""
        for record in self:
            if record.related_patient_id:
                # First check: Customer email cannot be empty when patient is linked
                if not record.email:
                    raise ValidationError(
                        "Email is required when a patient is linked to this customer!"
                    )

                # Second check: Patient must have an email
                if not record.related_patient_id.email:
                    raise ValidationError(
                        "Cannot link to a patient without an email address. "
                        "Patient email cannot be empty!"
                    )

                # Third check: Customer email must match patient email
                if record.email != record.related_patient_id.email:
                    raise ValidationError(
                        f"Cannot link customer with email '{record.email}' "
                        f"to patient with email '{record.related_patient_id.email}'. "
                        f"Customer and patient must have the same email address!"
                    )

    @api.constrains("related_patient_id")
    def _check_patient_not_linked_elsewhere(self):
        """Prevent linking patient that is already linked to another customer"""
        for record in self:
            if record.related_patient_id:
                # Check if this patient is already linked to another customer
                existing_customer = self.search(
                    [
                        ("related_patient_id", "=", record.related_patient_id.id),
                        ("id", "!=", record.id),
                    ],
                    limit=1,
                )  # Add limit=1 to ensure we get only one record

                if existing_customer:
                    raise ValidationError(
                        f"Patient '{record.related_patient_id.first_name} "
                        f"{record.related_patient_id.last_name}' is already linked "
                        f"to customer '{existing_customer.name}'. "
                        f"A patient can only be linked to one customer."
                    )

    def unlink(self):
        """Prevent deletion of customers linked to patients"""
        for record in self:
            if record.related_patient_id:
                raise UserError(
                    f"Cannot delete customer '{record.name}' because it's linked "
                    f"to patient '{record.related_patient_id.first_name} "
                    f"{record.related_patient_id.last_name}'. "
                    f"Please unlink the patient first."
                )
        return super(ResPartner, self).unlink()

    @api.onchange("related_patient_id")
    def _onchange_related_patient_id(self):
        """Auto-populate customer data from patient when linked"""
        if self.related_patient_id:
            patient = self.related_patient_id
            if not self.name:
                self.name = f"{patient.first_name} {patient.last_name}"
            if not self.email and patient.email:
                self.email = patient.email
