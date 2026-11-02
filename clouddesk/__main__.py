"""Command line: python -m clouddesk "ticket text"   |   python -m clouddesk --audit"""
import argparse
import json
import sys

from . import db
from .agent import triage
from .iam import default_iam
from .llm import LLMError


def main() -> int:
    ap = argparse.ArgumentParser(prog="clouddesk", description="Triage an IT/cloud support ticket.")
    ap.add_argument("ticket", nargs="?", help="ticket text (reads stdin if omitted)")
    ap.add_argument("--audit", action="store_true", help="run the IAM access audit instead")
    ap.add_argument("--report", action="store_true", help="print the SQL category report instead")
    args = ap.parse_args()

    if args.audit:
        print(json.dumps(default_iam().audit(), indent=2))
        return 0
    if args.report:
        print(json.dumps(db.category_report(db.connect()), indent=2))
        return 0
    text = args.ticket or sys.stdin.read()
    if not text.strip():
        ap.error("no ticket text given")
    try:
        print(json.dumps(triage(text), indent=2))
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
