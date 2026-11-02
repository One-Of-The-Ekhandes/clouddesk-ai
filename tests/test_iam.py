from clouddesk.iam import default_iam


def test_denied_action_recommends_least_privilege_group():
    r = default_iam().check_access("pnair", "lambda:UpdateFunctionCode")
    assert r["allowed"] is False
    assert "dev-deployers" in r["groups_that_grant"]
    assert "dev-deployers" in r["recommendation"]


def test_readonly_group_allows_reads_not_writes():
    iam = default_iam()
    assert iam.check_access("jmurphy", "s3:GetObject")["allowed"] is True
    assert iam.check_access("jmurphy", "s3:PutObject")["allowed"] is False


def test_production_write_is_escalated():
    r = default_iam().check_access("ochen", "dynamodb:PutItem")
    assert r["allowed"] is False
    assert r["groups_that_grant"] == ["prod-operators"]
    assert "escalate" in r["recommendation"].lower()


def test_power_user_cannot_touch_iam():
    r = default_iam().check_access("lfernandez", "iam:CreateUser")
    assert r["allowed"] is False
    assert "Escalate" in r["recommendation"]


def test_unknown_user():
    assert default_iam().check_access("ghost", "s3:GetObject")["found"] is False


def test_audit_flags_admin_direct_policy_and_missing_mfa():
    findings = {(f["user"], f["issue"].split(":")[0]) for f in default_iam().audit()}
    assert ("dryan", "Has AdministratorAccess") in findings
    assert ("dryan", "Policies attached directly to the user") in findings
    assert ("cwalsh", "Has AWS access without MFA") in findings
    # tkelly has no MFA but also no AWS access, so no finding
    assert not any(u == "tkelly" for u, _ in findings)
