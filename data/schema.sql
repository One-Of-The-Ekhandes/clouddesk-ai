-- CloudDesk AI schema (SQLite). All data in this repo is synthetic.

CREATE TABLE IF NOT EXISTS users (
    id                INTEGER PRIMARY KEY,
    username          TEXT NOT NULL UNIQUE,
    full_name         TEXT NOT NULL,
    email             TEXT NOT NULL UNIQUE,
    department        TEXT NOT NULL,
    account_status    TEXT NOT NULL CHECK (account_status IN ('active', 'locked', 'disabled')),
    mfa_enabled       INTEGER NOT NULL DEFAULT 1,
    password_last_set TEXT NOT NULL,
    last_login        TEXT
);

CREATE TABLE IF NOT EXISTS tickets (
    id          INTEGER PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    created_at  TEXT NOT NULL,
    category    TEXT NOT NULL,
    priority    TEXT NOT NULL CHECK (priority IN ('P1', 'P2', 'P3', 'P4')),
    subject     TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'escalated')),
    resolution  TEXT
);

-- Every agent decision is logged so its accuracy can be reviewed later.
CREATE TABLE IF NOT EXISTS triage_log (
    id           INTEGER PRIMARY KEY,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    ticket_text  TEXT NOT NULL,
    category     TEXT NOT NULL,
    priority     TEXT NOT NULL,
    escalate     INTEGER NOT NULL,
    assigned_team TEXT NOT NULL,
    tools_used   TEXT NOT NULL,
    provider     TEXT NOT NULL,
    latency_ms   INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category, status);
