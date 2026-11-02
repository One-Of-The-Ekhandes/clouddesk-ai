"""Score the triage agent against a labelled ticket set.

Usage:
    python -m evals.run_evals                 # provider from .env (mock if no key)
    python -m evals.run_evals --limit 10      # first 10 tickets (saves free-tier tokens)
    python -m evals.run_evals --min-category 0.8   # exit 1 if category accuracy is below 0.8 (CI gate)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

from clouddesk import db
from clouddesk.agent import triage
from clouddesk.config import ROOT, get_settings
from clouddesk.llm import LLMError

PRIORITY_RANK = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}


def load_cases(path: Path, limit: int | None) -> list[dict]:
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return cases[:limit] if limit else cases


def score(cases: list[dict], results: list[dict | None]) -> dict:
    n = len(cases)
    ok = [(c, r) for c, r in zip(cases, results) if r is not None]
    tp = sum(1 for c, r in ok if r["escalate"] and c["team"] != "service_desk")
    fp = sum(1 for c, r in ok if r["escalate"] and c["team"] == "service_desk")
    fn = sum(1 for c, r in ok if not r["escalate"] and c["team"] != "service_desk")
    tools_needed = [(c, r) for c, r in ok if c["must_use"]]
    return {
        "cases": n,
        "errors": n - len(ok),
        "category_accuracy": round(sum(r["category"] == c["category"] for c, r in ok) / n, 3),
        "priority_accuracy": round(sum(r["priority"] == c["priority"] for c, r in ok) / n, 3),
        "priority_within_one": round(sum(abs(PRIORITY_RANK[r["priority"]] - PRIORITY_RANK[c["priority"]]) <= 1
                                         for c, r in ok) / n, 3),
        "team_accuracy": round(sum(r["assigned_team"] == c["team"] for c, r in ok) / n, 3),
        "escalation_precision": round(tp / (tp + fp), 3) if tp + fp else None,
        "escalation_recall": round(tp / (tp + fn), 3) if tp + fn else None,
        "required_tool_use": round(sum(set(c["must_use"]) <= set(r["tools_used"]) for c, r in tools_needed)
                                   / len(tools_needed), 3) if tools_needed else None,
        "guardrail_corrections": sum(bool(r["guardrails"]) for _, r in ok),
        "avg_latency_ms": int(sum(r["latency_ms"] for _, r in ok) / len(ok)) if ok else None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cases", type=Path, default=ROOT / "evals" / "tickets.jsonl")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between tickets (free-tier rate limits)")
    ap.add_argument("--min-category", type=float, default=0.0)
    ap.add_argument("--out", type=Path, default=ROOT / "reports" / "eval_results.json")
    args = ap.parse_args(argv)

    settings = get_settings()
    cases = load_cases(args.cases, args.limit)
    conn = db.connect(":memory:")
    results: list[dict | None] = []
    mistakes = []
    for c in cases:
        try:
            r = triage(c["ticket"], conn=conn, settings=settings, log=False)
        except LLMError as exc:
            print(f"  #{c['id']}: ERROR {exc}", file=sys.stderr)
            r = None
        results.append(r)
        if r and (r["category"], r["priority"], r["assigned_team"]) != (c["category"], c["priority"], c["team"]):
            mistakes.append({"id": c["id"], "ticket": c["ticket"],
                             "expected": [c["category"], c["priority"], c["team"]],
                             "got": [r["category"], r["priority"], r["assigned_team"]]})
        if args.delay:
            time.sleep(args.delay)

    summary = {"provider": settings.provider, "model": settings.model, **score(cases, results)}
    args.out.parent.mkdir(exist_ok=True)
    args.out.write_text(json.dumps({"summary": summary, "mistakes": mistakes}, indent=2), encoding="utf-8")

    print(f"\nCloudDesk eval: {summary['provider']} / {summary['model']} on {summary['cases']} tickets")
    for k, v in summary.items():
        if k not in ("provider", "model", "cases"):
            print(f"  {k:<22} {v}")
    print(f"  mistakes listed in {args.out}")
    counts = Counter(m["expected"][0] for m in mistakes)
    if counts:
        print("  mistakes by category: " + ", ".join(f"{k} {v}" for k, v in counts.most_common()))
    return 1 if summary["category_accuracy"] < args.min_category else 0


if __name__ == "__main__":
    sys.exit(main())
