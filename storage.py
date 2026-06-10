import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Dict, Iterator

from config import Settings


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numberplate TEXT NOT NULL UNIQUE,
    email TEXT,
    phonenumber TEXT,
    notification_sent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(Settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(CREATE_TABLE_SQL)


def save_violation(numberplate: str, email: str = "", phonenumber: str = "", notification_sent: bool = False) -> Dict:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT * FROM violations WHERE numberplate = ?",
            (numberplate,),
        ).fetchone()
        if existing:
            return {
                "created": False,
                "record": dict(existing),
            }

        conn.execute(
            """
            INSERT INTO violations (numberplate, email, phonenumber, notification_sent, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (numberplate, email, phonenumber, int(notification_sent), now),
        )
        row = conn.execute(
            "SELECT * FROM violations WHERE numberplate = ?",
            (numberplate,),
        ).fetchone()
        return {
            "created": True,
            "record": dict(row),
        }
