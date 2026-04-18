from app.database.connection import get_connection

CREATE_LEADS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    company TEXT,
    role TEXT,
    source TEXT,
    score INTEGER,
    priority TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(CREATE_LEADS_TABLE_SQL)
        connection.commit()
