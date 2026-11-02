from clouddesk import db


def test_seeded_users(conn):
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 12


def test_find_user_by_username_email_and_name(conn):
    assert db.find_user(conn, "aoconnor")["account_status"] == "locked"
    assert db.find_user(conn, "Priya.Nair@example.com")["username"] == "pnair"
    assert db.find_user(conn, "tom kelly")["mfa_enabled"] == 0
    assert db.find_user(conn, "nobody") is None


def test_ticket_history_newest_first(conn):
    hist = db.user_ticket_history(conn, "aoconnor")
    assert [t["id"] for t in hist] == [2, 1]


def test_category_report_counts(conn):
    report = {r["category"]: r for r in db.category_report(conn)}
    assert report["cloud_access"]["total"] == 4
    assert report["cloud_access"]["escalated"] == 2
    assert report["cloud_access"]["escalation_pct"] == 50.0


def test_triage_log_roundtrip(conn):
    result = {"category": "network", "priority": "P3", "escalate": False,
              "assigned_team": "service_desk", "tools_used": ["search_kb"]}
    db.log_triage(conn, "VPN keeps dropping", result, "mock", 12)
    stats = db.triage_stats(conn)
    assert stats == [{"category": "network", "priority": "P3", "n": 1, "escalated": 0, "avg_latency_ms": 12}]
