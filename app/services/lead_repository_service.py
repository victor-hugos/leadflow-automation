from app.database.connection import get_connection
from app.models.lead import LeadProcessedData


def save_lead(lead: LeadProcessedData) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO leads (name, email, phone, company, role, source, score, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead.name,
                lead.email,
                lead.phone,
                lead.company,
                lead.role,
                lead.source,
                lead.score,
                lead.priority,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
