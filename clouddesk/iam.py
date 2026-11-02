"""IAM access checker and audit.

Two backends with the same interface:
- SnapshotIam: offline, reads data/iam_snapshot.json (used in tests, CI and demos).
- AwsIam: live and read-only, uses boto3 and the AWS IAM policy simulator.
"""
from __future__ import annotations

import json
from fnmatch import fnmatchcase
from functools import lru_cache
from pathlib import Path

from .config import get_settings


def _matches(action: str, patterns: list[str]) -> bool:
    action = action.lower()
    return any(fnmatchcase(action, p.lower()) for p in patterns)


class SnapshotIam:
    def __init__(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.policies = data["policies"]
        self.groups = data["groups"]
        self.users = data["users"]

    def _policies_allow(self, policy_names: list[str], action: str) -> bool:
        allowed = denied = False
        for name in policy_names:
            p = self.policies.get(name, {"allow": [], "deny": []})
            allowed |= _matches(action, p["allow"])
            denied |= _matches(action, p["deny"])
        return allowed and not denied

    def check_access(self, username: str, action: str) -> dict:
        user = self.users.get(username.lower())
        if user is None:
            return {"username": username, "action": action, "found": False,
                    "recommendation": "No IAM user with this name. Confirm the username or whether they use SSO."}
        granted_by = [g for g in user["groups"] if self._policies_allow(self.groups[g]["policies"], action)]
        granted_by += [p for p in user["attached_policies"] if self._policies_allow([p], action)]
        candidates = [g for g in self.groups
                      if g not in user["groups"] and self._policies_allow(self.groups[g]["policies"], action)]
        return _result(username, action, user["groups"], granted_by, candidates,
                       {g: self.groups[g].get("privileged", False) for g in candidates})

    def audit(self) -> list[dict]:
        findings = []
        for name, u in sorted(self.users.items()):
            effective = set(u["attached_policies"])
            for g in u["groups"]:
                effective.update(self.groups[g]["policies"])
            if "AdministratorAccess" in effective:
                findings.append(_finding("high", name, "Has AdministratorAccess", "Remove admin rights; use a scoped group."))
            if u["attached_policies"]:
                findings.append(_finding("medium", name, "Policies attached directly to the user: " + ", ".join(u["attached_policies"]),
                                         "Grant access through groups only."))
            if not u["mfa"] and (u["groups"] or u["attached_policies"]):
                findings.append(_finding("high", name, "Has AWS access without MFA", "Enforce MFA before access is used."))
        return findings


class AwsIam:
    """Live, read-only checks. Needs iam:List*, iam:Get* and iam:SimulatePrincipalPolicy."""

    def __init__(self, client=None):
        import boto3
        self.iam = client or boto3.client("iam")

    def check_access(self, username: str, action: str) -> dict:
        try:
            user_arn = self.iam.get_user(UserName=username)["User"]["Arn"]
        except self.iam.exceptions.NoSuchEntityException:
            return {"username": username, "action": action, "found": False,
                    "recommendation": "No IAM user with this name. Confirm the username or whether they use SSO."}
        groups = [g["GroupName"] for g in self.iam.list_groups_for_user(UserName=username)["Groups"]]
        allowed = self._simulate(user_arn, action)
        granted_by = groups if allowed else []
        candidates = []
        if not allowed:
            for g in self.iam.list_groups()["Groups"]:
                if g["GroupName"] not in groups and self._simulate(g["Arn"], action):
                    candidates.append(g["GroupName"])
        return _result(username, action, groups, granted_by, candidates,
                       {g: g.startswith("prod") for g in candidates})

    def _simulate(self, arn: str, action: str) -> bool:
        res = self.iam.simulate_principal_policy(PolicySourceArn=arn, ActionNames=[action])
        return res["EvaluationResults"][0]["EvalDecision"] == "allowed"

    def audit(self) -> list[dict]:
        findings = []
        for u in self.iam.list_users()["Users"]:
            name = u["UserName"]
            attached = [p["PolicyName"] for p in self.iam.list_attached_user_policies(UserName=name)["AttachedPolicies"]]
            group_policies = []
            for g in self.iam.list_groups_for_user(UserName=name)["Groups"]:
                group_policies += [p["PolicyName"] for p in
                                   self.iam.list_attached_group_policies(GroupName=g["GroupName"])["AttachedPolicies"]]
            if "AdministratorAccess" in attached + group_policies:
                findings.append(_finding("high", name, "Has AdministratorAccess", "Remove admin rights; use a scoped group."))
            if attached:
                findings.append(_finding("medium", name, "Policies attached directly to the user: " + ", ".join(attached),
                                         "Grant access through groups only."))
            if not self.iam.list_mfa_devices(UserName=name)["MFADevices"]:
                findings.append(_finding("high", name, "No MFA device", "Enforce MFA."))
        return findings


def _result(username, action, groups, granted_by, candidates, privileged) -> dict:
    allowed = bool(granted_by)
    if allowed:
        rec = f"Already allowed via {', '.join(granted_by)}. Check the resource policy or the region if it still fails."
    elif not candidates:
        rec = "No existing group grants this action. Escalate to the cloud team with the action, resource and business reason."
    elif all(privileged[c] for c in candidates):
        rec = (f"Only privileged group(s) grant this: {', '.join(candidates)}. "
               "Needs manager approval and cloud team sign-off; escalate.")
    else:
        safe = [c for c in candidates if not privileged[c]]
        rec = f"Add the user to group '{safe[0]}' (least privilege). Service desk can action this for non-production."
    return {"username": username, "action": action, "found": True, "groups": groups, "allowed": allowed,
            "granted_by": granted_by, "groups_that_grant": candidates, "recommendation": rec}


def _finding(severity: str, user: str, issue: str, fix: str) -> dict:
    return {"severity": severity, "user": user, "issue": issue, "fix": fix}


@lru_cache(maxsize=1)
def default_iam():
    s = get_settings()
    return AwsIam() if s.iam_source == "aws" else SnapshotIam(s.iam_snapshot)
