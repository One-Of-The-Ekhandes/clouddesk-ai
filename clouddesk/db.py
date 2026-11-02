"""SQLite access layer: user lookups, ticket history, triage logging and reports."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .config import ROOT, get_settings

SCHEMA = ROOT / "data" / "schema.sql"
SEED = ROOT / "data" / "seed.sql"


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    """Open the database, creating and seeding it on first use."""
    path = Path(path or get_settings().db_path)
    fresh = str(path) == ":memory:" or not path.exists()
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    if fresh:
        init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.executescript(SEED.read_text(encoding="utf-8"))
    conn.commit()


def find_user(conn: sqlite3.Connection, identifier: str) -> dict | None:
    """Find a user by username, email or full name (case-insensitive)."""
    ident = identifier.strip().lower()
    row = conn.execute(
        """SELECT username, full_name, email, department, account_status,
                  mfa_enabled, password_last_set, last_login
           FROM users
           WHERE lower(username) = ? OR lower(email) = ? OR lower(full_name) = ?""",
        (ident, ident, ident),
    ).fetchone()
    return dict(row) if row else None


def user_ticket_history(conn: sqlite3.Connection, identifier: str, limit: int = 5) -> list[dict]:
    """Most recent tickets for a user, newest first."""
    ident = identifier.strip().lower()
    rows = conn.execute(
        """SELECT t.id, t.created_at, t.category, t.priority, t.subject, t.status, t.resolution
           FROM tickets t
           JOIN users u ON u.id = t.user_id
           WHERE lower(u.username) = ? OR lower(u.email) = ? OR lower(u.full_name) = ?
           ORDER BY t.created_at DESC, t.id DESC
           LIMIT ?""",
        (ident, ident, ident, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def category_report(conn: sqlite3.Connection) -> list[dict]:
    """Ticket volume per category with resolution and escalation rates."""
    rows = conn.execute(
        """SELECT category,
                  COUNT(*) AS total,
                  SUM(status = 'resolved')  AS resolved,
                  SUM(status = 'escalated') AS escalated,
                  SUM(status = 'open')      AS open,
                  ROUND(100.0 * SUM(status = 'escalated') / COUNT(*), 1) AS escalation_pct
           FROM tickets
           GROUP BY category
           ORDER BY total DESC, category"""
    ).fetchall()
    return [dict(r) for r in rows]


def log_triage(conn: sqlite3.Connection, ticket_text: str, result: dict, provider: str, latency_ms: int) -> int:
    cur = conn.execute(
        """INSERT INTO triage_log (ticket_text, category, priority, escalate, assigned_team,
                                   tools_used, provider, latency_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ticket_text,
            result["category"],
            result["priority"],
            int(bool(result["escalate"])),
            result["assigned_team"],
            json.dumps(result.get("tools_used", [])),
            provider,
            latency_ms,
        ),
    )
    conn.commit()
    return cur.lastrowid


def triage_stats(conn: sqlite3.Connection) -> list[dict]:
    """Agent decisions per category and priority, from the triage log."""
    rows = conn.execute(
        """SELECT category, priority, COUNT(*) AS n,
                  SUM(escalate) AS escalated,
                  CAST(AVG(latency_ms) AS INTEGER) AS avg_latency_ms
           FROM triage_log
           GROUP BY category, priority
           ORDER BY n DESC"""
    ).fetchall()
    return [dict(r) for r in rows]
