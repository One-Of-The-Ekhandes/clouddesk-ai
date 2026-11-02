# Cost estimate

Goal: run the public demo for EUR 0 per month, with a hard alert before any spend.

| Service | What it does here | Free allowance | Expected demo usage | Monthly cost |
|---|---|---|---|---|
| AWS Lambda | Runs the API | 1M requests and 400,000 GB-seconds per month (always free) | < 5,000 requests | 0 |
| API Gateway HTTP API | Public HTTPS endpoint | 1M calls per month for the first 12 months on accounts that qualify for the legacy free tier | < 5,000 calls | 0 (about USD 0.005 after the free tier) |
| CloudWatch Logs | Lambda logs, 7-day retention | 5 GB ingestion | < 50 MB | 0 |
| SSM Parameter Store | API key (standard SecureString) | Standard parameters have no charge | 1 parameter | 0 |
| AWS Budgets | Cost alert | First 2 budgets free | 1 budget | 0 |
| Groq API | LLM inference | Free tier with rate and daily token limits | ~3 LLM calls per ticket | 0 |
| GitHub Actions | CI | Free for public repositories | ~10 runs per day | 0 |
| Streamlit Community Cloud | Demo UI | Free for public apps | 1 app | 0 |

AWS free-tier terms differ by account age and type. Check the current terms for your own account; the budget alarm sends an email if forecast spend passes USD 1.

## Controls that keep it free

- API Gateway throttling: burst 5, steady 2 requests per second.
- Lambda timeout 29 seconds and 512 MB memory.
- Log retention 7 days.
- Tool results trimmed (articles cut to 700 characters, top 2 results) to save LLM tokens.
- The eval runner has `--limit` and `--delay` flags for free-tier rate limits.

## At company scale (illustrative)

For 2,000 tickets a day the main cost is the LLM, not AWS. At roughly 3 calls and about 4,000 tokens per ticket, that is about 240 million tokens a month. The bill depends on the model: a small model costs a few euro per month, and a frontier model costs more. The design lets you switch providers through one environment variable, so the trade-off between cost and accuracy can be measured with the eval set before choosing.
