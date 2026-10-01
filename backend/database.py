import sqlite3
from backend.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they do not exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT    NOT NULL,
            file_hash   TEXT    UNIQUE NOT NULL,
            page_count  INTEGER,
            chunk_count INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            normalized_question TEXT UNIQUE NOT NULL,
            answer              TEXT,
            sources             TEXT,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            question             TEXT,
            answer               TEXT,
            response_time_ms     REAL,
            retrieved_chunk_count INTEGER,
            cache_hit            INTEGER,
            timestamp            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
