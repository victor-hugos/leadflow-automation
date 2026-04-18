def classify_lead_priority(score: int) -> str:
    if score <= 20:
        return "low"
    if score <= 40:
        return "medium"
    return "high"
