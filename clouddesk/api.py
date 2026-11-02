"""REST API (FastAPI). Run locally: uvicorn clouddesk.api:app --reload"""
from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from . import __version__, db
from .agent import triage
from .config import get_settings
from .iam import default_iam
from .llm import LLMError

app = FastAPI(title="CloudDesk AI", version=__version__,
              description="LLM service-desk agent for IT and cloud support tickets.")
_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = db.connect()
    return _conn


class TicketIn(BaseModel):
    ticket: str = Field(min_length=5, max_length=4000,
                        examples=["I'm locked out of my account. aoife.oconnor@example.com"])


@app.get("/health")
def health():
    s = get_settings()
    return {"status": "ok", "version": __version__, "provider": s.provider, "model": s.model}


@app.post("/triage")
def triage_ticket(body: TicketIn, conn=Depends(get_conn)):
    try:
        return triage(body.ticket, conn=conn)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/reports/categories")
def report_categories(conn=Depends(get_conn)):
    return db.category_report(conn)


@app.get("/reports/triage")
def report_triage(conn=Depends(get_conn)):
    return db.triage_stats(conn)


@app.get("/iam/check")
def iam_check(user: str = Query(..., description="Username or email"),
              action: str = Query(..., pattern=r"^[a-z0-9-]+:[A-Za-z*]+$"), conn=Depends(get_conn)):
    found = db.find_user(conn, user)
    return default_iam().check_access(found["username"] if found else user.split("@")[0], action)


@app.get("/iam/audit")
def iam_audit():
    return default_iam().audit()
