from app.models.lead import LeadCreate

PUBLIC_EMAIL_DOMAINS = {
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "yahoo.com",
    "yahoo.com.br",
}


def is_corporate_email(email: str) -> bool:
    domain = email.split("@")[-1].strip().lower()
    return domain not in PUBLIC_EMAIL_DOMAINS


def calculate_lead_score(lead: LeadCreate) -> int:
    score = 0

    if is_corporate_email(lead.email):
        score += 20
    if lead.phone:
        score += 10
    if lead.company:
        score += 20
    if lead.role:
        score += 10

    return score
