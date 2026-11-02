import pytest
from fastapi.testclient import TestClient

from clouddesk import api, db


@pytest.fixture
def client(conn):
    api.app.dependency_overrides[api.get_conn] = lambda: conn
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["provider"] == "mock"


def test_triage_endpoint(client):
    r = client.post("/triage", json={"ticket": "Checkout API returning 503 errors for all customers"})
    assert r.status_code == 200
    assert r.json()["priority"] == "P1"


def test_triage_rejects_empty_ticket(client):
    assert client.post("/triage", json={"ticket": ""}).status_code == 422


def test_reports(client):
    client.post("/triage", json={"ticket": "VPN keeps dropping every 10 minutes"})
    cats = client.get("/reports/categories").json()
    assert any(c["category"] == "cloud_access" for c in cats)
    assert client.get("/reports/triage").json()[0]["n"] == 1


def test_iam_endpoints(client):
    r = client.get("/iam/check", params={"user": "priya.nair@example.com", "action": "lambda:UpdateFunctionCode"})
    assert r.json()["allowed"] is False
    assert client.get("/iam/check", params={"user": "pnair", "action": "not an action"}).status_code == 422
    assert any(f["user"] == "dryan" for f in client.get("/iam/audit").json())
