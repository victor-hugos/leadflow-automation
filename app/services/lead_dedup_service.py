from app.database.connection import get_connection


def lead_exists_by_email(email: str) -> bool:
    normalized_email = email.strip().lower()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT 1
            FROM leads
            WHERE lower(email) = ?
            LIMIT 1
            """,
            (normalized_email,),
        ).fetchone()

    return row is not None
