import re

from app.models.lead import LeadCreate

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_lead_business_rules(lead: LeadCreate) -> list[str]:
    errors: list[str] = []

    if not lead.name.strip():
        errors.append("Name cannot be empty")

    if not EMAIL_PATTERN.match(lead.email.strip()):
        errors.append("Email format is invalid")

    if lead.phone is not None:
        phone_digits = "".join(char for char in lead.phone if char.isdigit())
        if len(phone_digits) < 10:
            errors.append("Phone must have at least 10 digits")

    return errors
