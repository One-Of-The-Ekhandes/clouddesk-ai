"""The triage agent: an LLM tool-calling loop plus rule-based guardrails."""
from __future__ import annotations

import json
import re
import sqlite3
import time
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from . import db
from .config import Settings, get_settings
from .llm import LLMError, MockChatClient, OpenAIChatClient, ToolCallRejected
from .tools import TOOL_SPECS, run_tool

Category = Literal["account_access", "cloud_access", "email", "network", "hardware", "software", "security", "outage"]
Priority = Literal["P1", "P2", "P3", "P4"]
Team = Literal["service_desk", "cloud_team", "security_team", "network_team", "incident_management"]

SYSTEM_PROMPT = """You are CloudDesk, a first-line IT and cloud service-desk agent.
Investigate the ticket with your tools before deciding: search the knowledge base, look up the user
when an email or username is given, and check AWS IAM access when the ticket names an AWS action or resource.

Categories:
- outage: a service is down or failing for many users or customers (including company-wide email or chat).
- security: possible compromise or data exposure: phishing, unexpected MFA prompts, suspicious mailbox
  forwarding rules, leaked keys, public buckets, malware alerts.
- cloud_access: AWS permissions and access requests. account_access: sign-in, passwords, lockouts, MFA setup.
- email, network, hardware, software: problems or requests for one user in that area.

Priorities:
- P1: production outage or service down affecting customers or many users.
- P2: security incident, or one user fully blocked with an urgent business deadline, or a whole floor/site affected.
- P3: one user impaired with a standard fix (lockout, VPN, an AccessDenied error, email problems).
- P4: requests and how-to questions (software installs, licences, requests for new access or equipment),
  even when the request is for work. A request is not an incident unless something is broken.

Teams: service_desk (handles it directly, including adding users to read-only AWS groups), cloud_team
(AWS deploy rights, production access, admin requests and anything no read-only group grants), security_team (any possible security incident), network_team (site-wide network
problems), incident_management (outages).

When you have decided, call the submit_triage tool with your decision. Its fields are:
{"category": one of account_access|cloud_access|email|network|hardware|software|security|outage,
 "priority": "P1"|"P2"|"P3"|"P4",
 "assigned_team": one of the teams above,
 "escalate": true if assigned_team is not service_desk,
 "summary": one sentence,
 "reply_to_user": a short, friendly reply with the next steps for the user,
 "internal_notes": what you checked and found, for the engineer}"""


NUDGE = ("Use only the tools provided. When you have decided, call submit_triage with your decision "
         "(category, priority, assigned_team, escalate, summary, reply_to_user, internal_notes).")

SUBMIT_TOOL = {"type": "function", "function": {
    "name": "submit_triage",
    "description": "Submit the final triage decision. Call this exactly once, after investigating.",
    "parameters": {"type": "object", "properties": {
        "category": {"type": "string", "enum": list(Category.__args__)},
        "priority": {"type": "string", "enum": list(Priority.__args__)},
        "assigned_team": {"type": "string", "enum": list(Team.__args__)},
        "escalate": {"type": "boolean"},
        "summary": {"type": "string"},
        "reply_to_user": {"type": "string"},
        "internal_notes": {"type": "string"}},
        "required": ["category", "priority", "assigned_team", "escalate", "summary", "reply_to_user"]}}}


class Triage(BaseModel):
    category: Category
    priority: Priority
    assigned_team: Team
    escalate: bool
    summary: str
    reply_to_user: str
    internal_notes: str = ""
    tools_used: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


def make_client(settings: Settings):
    return MockChatClient(settings) if settings.provider == "mock" else OpenAIChatClient(settings)


def _parse_json(content: str) -> dict:
    match = re.search(r"\{.*\}", content or "", re.S)
    if not match:
        raise ValueError("model did not return a JSON object")
    return json.loads(match.group(0))


def apply_guardrails(t: Triage, ticket: str) -> Triage:
    """Hard rules that hold whatever the model says. Each change is recorded."""
    notes = []
    if t.category == "outage" and t.priority != "P1":
        t.priority = "P1"; notes.append("outage forced to P1")
    if t.category == "outage" and t.assigned_team != "incident_management":
        t.assigned_team = "incident_management"; notes.append("outage routed to incident_management")
    if t.category == "security" and t.assigned_team != "security_team":
        t.assigned_team = "security_team"; notes.append("security routed to security_team")
    if t.category == "security" and t.priority in ("P3", "P4"):
        t.priority = "P2"; notes.append("security raised to P2")
    text = ticket.lower()
    if (t.category == "cloud_access" and re.search(r"\b(prod|production)\b", text)
            and re.search(r"\b(write|put|delete|modify|admin)\b", text) and t.assigned_team == "service_desk"):
        t.assigned_team = "cloud_team"; notes.append("production write access routed to cloud_team")
    if (t.category == "cloud_access" and re.search(r"\b(admin|administrator|administratoraccess)\b", text)
            and t.assigned_team == "service_desk"):
        t.assigned_team = "cloud_team"; notes.append("admin access request routed to cloud_team")
    if t.escalate != (t.assigned_team != "service_desk"):
        t.escalate = t.assigned_team != "service_desk"; notes.append("escalate flag aligned with team")
    t.guardrails = notes
    return t


def triage(ticket: str, conn: sqlite3.Connection | None = None, settings: Settings | None = None,
           client=None, max_turns: int = 6, log: bool = True) -> dict:
    settings = settings or get_settings()
    conn = conn or db.connect()
    client = client or make_client(settings)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": ticket}]
    tools_used: list[str] = []
    started = time.perf_counter()
    data = None
    nudges = 2  # times we remind the model to use submit_triage before giving up
    msg: dict = {}

    for _ in range(max_turns):
        try:
            msg = client.chat(messages, tools=TOOL_SPECS + [SUBMIT_TOOL])
        except ToolCallRejected:
            if not nudges:
                raise
            nudges -= 1
            messages.append({"role": "user", "content": NUDGE})
            continue
        calls = msg.get("tool_calls") or []
        if not calls:
            try:
                data = _parse_json(msg.get("content") or "")
                break
            except ValueError:
                if not nudges:
                    break
                nudges -= 1
                messages.append({"role": "assistant", "content": msg.get("content") or ""})
                messages.append({"role": "user", "content": NUDGE})
                continue
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": calls})
        for call in calls:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            if name == "submit_triage":
                data = args
                break
            result = run_tool(conn, name, args)
            tools_used.append(name)
            messages.append({"role": "tool", "tool_call_id": call["id"], "name": name,
                             "content": json.dumps(result, default=str)})
        if data is not None:
            break
    else:  # ran out of turns while still calling tools: ask for the answer without tools
        msg = client.chat(messages + [{"role": "user", "content": "Give your final decision now as a JSON object."}])

    try:
        if data is None:
            data = _parse_json(msg.get("content") or "")
        result = Triage(**{k: v for k, v in data.items() if k in Triage.model_fields}, tools_used=tools_used)
    except (ValueError, ValidationError) as exc:
        raise LLMError(f"Could not parse a valid triage answer: {exc}") from exc

    result = apply_guardrails(result, ticket)
    latency_ms = int((time.perf_counter() - started) * 1000)
    out = result.model_dump() | {"provider": settings.provider, "model": settings.model, "latency_ms": latency_ms}
    if log:
        out["log_id"] = db.log_triage(conn, ticket, out, settings.provider, latency_ms)
    return out
