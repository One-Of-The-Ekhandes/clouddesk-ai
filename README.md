# CloudDesk AI

[![CI](https://github.com/One-Of-The-Ekhandes/clouddesk-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/One-Of-The-Ekhandes/clouddesk-ai/actions/workflows/ci.yml)

An LLM agent that triages IT and cloud support tickets. It reads a ticket, investigates with tools, decides the category, priority and owning team, drafts a reply to the user, and escalates when a human engineer is needed. Every decision is checked against hard guardrails, logged to SQL, and measured against a labelled evaluation set.

All users, tickets and AWS accounts in this repository are synthetic.

## Why I built it

I spent two years on an IT service desk handling 40+ tickets a day in ServiceNow: account lockouts, Microsoft 365 issues and access requests, including AWS IAM groups and policies. The first diagnosis step follows the same pattern every time: read the ticket, check the user's account, look up the known fix, check their access, decide who owns it. CloudDesk AI automates that step and measures how often it gets it right.

## What it does

```text
$ python -m clouddesk "Getting AccessDenied for lambda:UpdateFunctionCode when deploying to dev. priya.nair@example.com"
{
  "category": "cloud_access",
  "priority": "P3",
  "assigned_team": "cloud_team",
  "escalate": true,
  "internal_notes": "Checked IAM access for priya.nair@example.com; user is in dev-readonly group and not
                     allowed lambda:UpdateFunctionCode. Recommend adding user to dev-deployers via cloud team.",
  "tools_used": ["check_iam_access"],
  ...
}
```

- **Agent with tool calling:** the LLM chooses between three tools: knowledge-base search, a SQL lookup of the user and their ticket history, and an AWS IAM access check. It submits its decision through a typed `submit_triage` tool, validated with Pydantic.
- **Guardrails in code:** rules the model cannot override (outages are P1 and go to incident management, security goes to the security team, production write and admin access go to the cloud team). Every correction is recorded.
- **IAM access checker and audit:** answers "can this user do X, and which group should they join?" using least privilege, and flags admin rights, policies attached directly to users, and access without MFA. Works offline on a snapshot or live against AWS through the read-only IAM policy simulator.
- **Evaluation:** 48 labelled tickets scored on category, priority, team, escalation precision and recall, and required tool use. CI runs it on every push.
- **Interfaces:** REST API (FastAPI), Streamlit demo, command line.
- **Cloud:** AWS Lambda behind API Gateway, built with Terraform, with the API key in SSM Parameter Store, a least-privilege IAM role, throttling, 7-day log retention and a USD 1 budget alarm.

## Results

Evaluated on the 48-ticket set in `evals/tickets.jsonl` (`python -m evals.run_evals`).

| Metric | Keyword baseline (no LLM) | LLM agent (run 3) |
|---|---|---|
| Category accuracy | 70.8% | **91.7%** |
| Priority accuracy (exact) | 56.2% | **87.5%** |
| Priority within one level | 91.7% | **100%** |
| Team accuracy | 79.2% | **91.7%** |
| Escalation recall (tickets that needed a human and got one) | 41.2% | **94.1%** |
| Escalation precision | 100% | 84.2% |
| Required tool used when needed | 100% | 100% |
| Failed runs | 0 / 48 | 0 / 48 |
| Average latency per ticket | < 1 ms | 5.6 s |

LLM: `openai/gpt-oss-120b` on Groq, 2 November 2026. The raw results for every run, including each mistake, are in [`evals/results/`](evals/results/).

The keyword baseline is the offline mock used in CI: simple rules with no LLM. It shows what the LLM adds, mainly in catching tickets that must be escalated.

The LLM's main gain over keyword rules is catching tickets that must go to a human (94% against 41%). Its precision is lower: it escalates a few borderline tickets the labels keep with the service desk, which is the safer direction to be wrong in.

What moved the numbers, run by run:

| Run | Change | Failed runs | Category accuracy |
|---|---|---|---|
| 1 | Final answer as free-text JSON | 10 / 48 | 77.1% |
| 2 | Typed `submit_triage` tool for the final answer | 7 / 48 | 81.2% |
| 3 | Reminder and retry when the model answers in prose or the provider rejects a malformed tool call | 0 / 48 | 91.7% |

After run 3 I reviewed the 11 remaining mistakes. Four were real errors in patterns (requests rated P3 instead of P4, an AWS admin request kept at the service desk), so I added clearer category and priority definitions and an admin-access guardrail. The others are borderline cases, such as whether a broken desk network port belongs to the service desk or the network team, and I left those labels unchanged rather than tune the test set to the model. A full rerun with these changes is limited by the Groq free tier (8,000 tokens per minute) and will be added to `evals/results/`.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the diagram, [docs/cost.md](docs/cost.md) for the cost estimate, and [docs/decisions.md](docs/decisions.md) for the design decisions.

```text
clouddesk/      agent, LLM client, tools, knowledge base, SQL layer, IAM checker, API, Lambda handler, CLI
data/           schema and seed SQL, knowledge-base articles, IAM snapshot
evals/          labelled tickets and the scoring runner
app/            Streamlit demo
infra/          Lambda build script and Terraform
tests/          38 tests (pytest), run offline
```

## Run it locally

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
copy .env.example .env            # add a free Groq or Gemini API key; leave it empty for the offline baseline

pytest                            # 38 tests, offline
python -m clouddesk "VPN disconnects every 10 minutes. rahul.mehta@example.com"
python -m evals.run_evals --delay 1.5
uvicorn clouddesk.api:app --reload        # API docs at http://localhost:8000/docs
streamlit run app/streamlit_app.py        # demo UI
```

## Deploy to AWS

```bash
python infra/build_lambda.py
cd infra/terraform
terraform init
terraform apply -var="budget_email=you@example.com" -var="llm_api_key=YOUR_KEY"
```

The output prints the API URL. `terraform destroy` removes everything.

## Built with

Python 3.12, FastAPI, Pydantic, SQLite, Streamlit, boto3, Terraform, Docker and GitHub Actions. The LLM is `openai/gpt-oss-120b` on Groq's free tier, and the provider can be switched to Gemini or a local Ollama model through one environment variable.

I built this project with Claude Code as an AI pair programmer, reviewing and testing every change.

## Author

Rujuta Ekhande · [LinkedIn](https://www.linkedin.com/in/rujuta-ekhande-93b257349) · [GitHub](https://github.com/One-Of-The-Ekhandes)

MIT License
