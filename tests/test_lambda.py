import json


def _event(method: str, path: str, body: dict | None = None) -> dict:
    """Minimal API Gateway HTTP API (payload v2) event."""
    return {
        "version": "2.0", "routeKey": "$default", "rawPath": path, "rawQueryString": "",
        "headers": {"content-type": "application/json", "host": "example.execute-api.eu-west-1.amazonaws.com"},
        "requestContext": {"http": {"method": method, "path": path, "protocol": "HTTP/1.1", "sourceIp": "127.0.0.1"},
                           "stage": "$default", "requestId": "test"},
        "body": json.dumps(body) if body else None, "isBase64Encoded": False,
    }


def test_lambda_handler_serves_api(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUDDESK_DB", str(tmp_path / "lambda.db"))
    from clouddesk.lambda_handler import handler

    health = handler(_event("GET", "/health"), None)
    assert health["statusCode"] == 200

    res = handler(_event("POST", "/triage", {"ticket": "The customer portal is returning 503 errors for everyone."}), None)
    assert res["statusCode"] == 200
    assert json.loads(res["body"])["priority"] == "P1"
