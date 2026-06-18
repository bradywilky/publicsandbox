import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utcnow_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            discord_user_id INTEGER PRIMARY KEY,
            google_refresh_token TEXT,
            google_access_token TEXT,
            google_token_expiry TEXT,
            google_calendar_id TEXT DEFAULT 'primary',
            timezone TEXT DEFAULT 'America/New_York',
            reminder_minutes TEXT DEFAULT '30,5',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS oauth_states (
            state TEXT PRIMARY KEY,
            discord_user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sent_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_user_id INTEGER NOT NULL,
            event_id TEXT NOT NULL,
            remind_at TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            UNIQUE(discord_user_id, event_id, remind_at)
        );
        """
    )
    conn.commit()


def upsert_user_if_missing(conn: sqlite3.Connection, discord_user_id: int) -> None:
    now = utcnow_iso()
    conn.execute(
        """
        INSERT INTO users(discord_user_id, created_at, updated_at)
        VALUES(?, ?, ?)
        ON CONFLICT(discord_user_id) DO UPDATE SET updated_at = excluded.updated_at
        """,
        (discord_user_id, now, now),
    )
    conn.commit()


def save_oauth_state(conn: sqlite3.Connection, state: str, discord_user_id: int) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO oauth_states(state, discord_user_id, created_at) VALUES(?, ?, ?)",
        (state, discord_user_id, utcnow_iso()),
    )
    conn.commit()


def pop_oauth_state(conn: sqlite3.Connection, state: str) -> int | None:
    row = conn.execute(
        "SELECT discord_user_id FROM oauth_states WHERE state = ?", (state,)
    ).fetchone()
    conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
    conn.commit()
    return int(row["discord_user_id"]) if row else None


def save_google_tokens(
    conn: sqlite3.Connection,
    discord_user_id: int,
    access_token: str | None,
    refresh_token: str | None,
    expiry_iso: str | None,
) -> None:
    now = utcnow_iso()
    conn.execute(
        """
        INSERT INTO users(discord_user_id, google_access_token, google_refresh_token, google_token_expiry, created_at, updated_at)
        VALUES(?, ?, ?, ?, ?, ?)
        ON CONFLICT(discord_user_id) DO UPDATE SET
            google_access_token = excluded.google_access_token,
            google_refresh_token = COALESCE(excluded.google_refresh_token, users.google_refresh_token),
            google_token_expiry = excluded.google_token_expiry,
            updated_at = excluded.updated_at
        """,
        (discord_user_id, access_token, refresh_token, expiry_iso, now, now),
    )
    conn.commit()


def get_user(conn: sqlite3.Connection, discord_user_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM users WHERE discord_user_id = ?", (discord_user_id,)
    ).fetchone()


def list_connected_users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT * FROM users
        WHERE google_refresh_token IS NOT NULL
        """
    ).fetchall()
    return list(rows)


def reminder_already_sent(
    conn: sqlite3.Connection, discord_user_id: int, event_id: str, remind_at: str
) -> bool:
    row = conn.execute(
        """
        SELECT id FROM sent_reminders
        WHERE discord_user_id = ? AND event_id = ? AND remind_at = ?
        """,
        (discord_user_id, event_id, remind_at),
    ).fetchone()
    return row is not None


def mark_reminder_sent(
    conn: sqlite3.Connection, discord_user_id: int, event_id: str, remind_at: str
) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO sent_reminders(discord_user_id, event_id, remind_at, sent_at)
        VALUES(?, ?, ?, ?)
        """,
        (discord_user_id, event_id, remind_at, utcnow_iso()),
    )
    conn.commit()


def update_reminder_minutes(
    conn: sqlite3.Connection, discord_user_id: int, reminder_minutes: str
) -> None:
    conn.execute(
        """
        UPDATE users SET reminder_minutes = ?, updated_at = ?
        WHERE discord_user_id = ?
        """,
        (reminder_minutes, utcnow_iso(), discord_user_id),
    )
    conn.commit()


def update_timezone(conn: sqlite3.Connection, discord_user_id: int, timezone_name: str) -> None:
    conn.execute(
        "UPDATE users SET timezone = ?, updated_at = ? WHERE discord_user_id = ?",
        (timezone_name, utcnow_iso(), discord_user_id),
    )
    conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}
