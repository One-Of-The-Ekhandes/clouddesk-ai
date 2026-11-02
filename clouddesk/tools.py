"""Tools the agent can call. Each returns compact JSON-serialisable data."""
from __future__ import annotations

import sqlite3

from . import db
from .iam import default_iam
from .kb import default_kb

TOOL_SPECS = [
    {"type": "function", "function": {
        "name": "search_kb",
        "description": "Search the IT knowledge base for known fixes and the team that owns an issue.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Short description of the problem"}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "lookup_user",
        "description": "Look up a user's directory account (status, MFA, last login) and their recent tickets.",
        "parameters": {"type": "object", "properties": {
            "identifier": {"type": "string", "description": "Username, email address or full name"}},
            "required": ["identifier"]}}},
    {"type": "function", "function": {
        "name": "check_iam_access",
        "description": ("Check whether a user is allowed an AWS action (for example s3:GetObject or "
                        "lambda:UpdateFunctionCode) and which IAM group would grant it."),
        "parameters": {"type": "object", "properties": {
            "identifier": {"type": "string", "description": "Username or email address"},
            "action": {"type": "string", "description": "AWS action in service:Action form"}},
            "required": ["identifier", "action"]}}},
]


def _resolve_username(conn: sqlite3.Connection, identifier: str) -> str:
    user = db.find_user(conn, identifier)
    return user["username"] if user else identifier.split("@")[0]


def run_tool(conn: sqlite3.Connection, name: str, args: dict) -> dict:
    if name == "search_kb":
        hits = default_kb().search(args.get("query", ""), k=2)
        # Trim article bodies so tool results stay small for free-tier token limits.
        return {"results": [{**h, "content": h["content"][:700]} for h in hits]}
    if name == "lookup_user":
        ident = args.get("identifier", "")
        user = db.find_user(conn, ident)
        if not user:
            return {"found": False, "identifier": ident}
        return {"found": True, "user": user, "recent_tickets": db.user_ticket_history(conn, ident, limit=3)}
    if name == "check_iam_access":
        username = _resolve_username(conn, args.get("identifier", ""))
        return default_iam().check_access(username, args.get("action", ""))
    return {"error": f"Unknown tool '{name}'"}
