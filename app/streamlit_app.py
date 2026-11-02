"""CloudDesk AI demo UI. Run: streamlit run app/streamlit_app.py"""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from clouddesk import db  # noqa: E402
from clouddesk.agent import triage  # noqa: E402
from clouddesk.config import ROOT, get_settings  # noqa: E402
from clouddesk.iam import default_iam  # noqa: E402
from clouddesk.llm import LLMError  # noqa: E402

st.set_page_config(page_title="CloudDesk AI", page_icon="🛠️", layout="wide")
settings = get_settings()

EXAMPLES = [
    "I'm locked out of my laptop again after changing my password yesterday. aoife.oconnor@example.com",
    "Getting AccessDenied for lambda:UpdateFunctionCode when deploying the orders service to dev. priya.nair@example.com",
    "I got an MFA prompt on my phone that I didn't trigger, three times this morning. tom.kelly@example.com",
    "The customer portal is returning 503 errors for everyone.",
    "Wi-Fi is down for the whole third floor, nobody can connect.",
]
PRIORITY_COLOUR = {"P1": "red", "P2": "orange", "P3": "blue", "P4": "gray"}


@st.cache_resource
def get_conn():
    return db.connect(":memory:")  # fresh demo database per app instance


conn = get_conn()

st.title("🛠️ CloudDesk AI")
st.caption(f"LLM service-desk agent for IT and cloud tickets · provider: **{settings.provider}** · "
           f"model: **{settings.model}** · all data is synthetic")
if settings.provider == "mock":
    st.info("Running the offline keyword baseline. Add a GROQ_API_KEY to use the real LLM agent.")

tab_triage, tab_iam, tab_reports, tab_evals = st.tabs(["Triage a ticket", "IAM access", "Reports", "Evaluation"])

with tab_triage:
    example = st.selectbox("Try an example", ["(write your own)"] + EXAMPLES)
    ticket = st.text_area("Ticket", value="" if example.startswith("(") else example, height=120)
    if st.button("Triage", type="primary", disabled=len(ticket.strip()) < 5):
        with st.spinner("Investigating..."):
            try:
                r = triage(ticket, conn=conn)
            except LLMError as exc:
                st.error(str(exc))
                st.stop()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Category", r["category"].replace("_", " "))
        c2.markdown(f"**Priority**  \n:{PRIORITY_COLOUR[r['priority']]}[**{r['priority']}**]")
        c3.metric("Team", r["assigned_team"].replace("_", " "))
        c4.metric("Escalate", "Yes" if r["escalate"] else "No")
        st.subheader("Reply to user")
        st.write(r["reply_to_user"])
        st.subheader("Internal notes")
        st.write(r["internal_notes"] or "-")
        st.caption(f"Tools used: {', '.join(r['tools_used']) or 'none'} · latency {r['latency_ms']} ms")
        if r["guardrails"]:
            st.warning("Guardrails applied: " + "; ".join(r["guardrails"]))

with tab_iam:
    left, right = st.columns(2)
    with left:
        st.subheader("Can this user do it?")
        user = st.text_input("User (username or email)", "priya.nair@example.com")
        action = st.text_input("AWS action", "lambda:UpdateFunctionCode")
        if st.button("Check access"):
            found = db.find_user(conn, user)
            st.json(default_iam().check_access(found["username"] if found else user.split("@")[0], action))
    with right:
        st.subheader("Access audit")
        st.dataframe(default_iam().audit(), use_container_width=True, hide_index=True)

with tab_reports:
    st.subheader("Ticket history by category (SQL report)")
    st.dataframe(db.category_report(conn), use_container_width=True, hide_index=True)
    st.subheader("Agent decisions this session")
    stats = db.triage_stats(conn)
    st.dataframe(stats, use_container_width=True, hide_index=True) if stats else st.write("No tickets triaged yet.")

with tab_evals:
    path = ROOT / "reports" / "eval_results.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        st.json(data["summary"])
        st.dataframe(data["mistakes"], use_container_width=True, hide_index=True)
    else:
        st.write("Run `python -m evals.run_evals` to generate results.")
