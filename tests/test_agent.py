import json

import pytest

from clouddesk.agent import Triage, apply_guardrails, triage
from clouddesk.llm import LLMError
from clouddesk.tools import run_tool


def test_lockout_ticket_uses_tools_and_stays_with_service_desk(conn):
    r = triage("I'm locked out of my account again. aoife.oconnor@example.com", conn=conn)
    assert r["category"] == "account_access"
    assert r["assigned_team"] == "service_desk" and r["escalate"] is False
    assert {"search_kb", "lookup_user"} <= set(r["tools_used"])
    assert "locked" in r["internal_notes"]


def test_aws_denied_ticket_checks_iam_and_escalates(conn):
    r = triage("Getting AccessDenied for lambda:UpdateFunctionCode when deploying to dev. "
               "priya.nair@example.com", conn=conn)
    assert r["category"] == "cloud_access"
    assert "check_iam_access" in r["tools_used"]
    assert r["escalate"] is True


def test_outage_is_p1(conn):
    r = triage("Checkout API returning 503 errors for all customers since 10am", conn=conn)
    assert (r["category"], r["priority"], r["assigned_team"]) == ("outage", "P1", "incident_management")


def test_triage_is_logged(conn):
    triage("Outlook shared mailbox is missing", conn=conn)
    assert conn.execute("SELECT COUNT(*) FROM triage_log").fetchone()[0] == 1


def test_guardrails_override_model_mistakes():
    t = Triage(category="security", priority="P4", assigned_team="service_desk", escalate=False,
               summary="s", reply_to_user="r")
    t = apply_guardrails(t, "I clicked a phishing link")
    assert (t.priority, t.assigned_team, t.escalate) == ("P2", "security_team", True)
    assert t.guardrails


def test_tool_iam_accepts_email(conn):
    r = run_tool(conn, "check_iam_access", {"identifier": "james.murphy@example.com", "action": "s3:GetObject"})
    assert r["username"] == "jmurphy" and r["allowed"] is True


class BadClient:
    def chat(self, messages, tools=None):
        return {"role": "assistant", "content": "I think it's a network issue"}


def test_unparseable_answer_raises(conn):
    with pytest.raises(LLMError):
        triage("VPN down", conn=conn, client=BadClient())


class ToolLoopingClient:
    """Keeps calling tools; the agent must stop and ask for a final answer."""
    def chat(self, messages, tools=None):
        if tools:
            return {"role": "assistant", "content": None, "tool_calls": [
                {"id": "c1", "type": "function", "function": {"name": "search_kb", "arguments": json.dumps({"query": "vpn"})}}]}
        return {"role": "assistant", "content": json.dumps({
            "category": "network", "priority": "P3", "assigned_team": "service_desk", "escalate": False,
            "summary": "VPN", "reply_to_user": "ok"})}


def test_max_turns_forces_final_answer(conn):
    r = triage("VPN keeps dropping", conn=conn, client=ToolLoopingClient(), max_turns=2)
    assert r["category"] == "network" and r["tools_used"] == ["search_kb", "search_kb"]
