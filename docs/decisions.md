# Design decisions

**1. One OpenAI-compatible client instead of one SDK per provider.**
Groq, Gemini and Ollama all accept the same chat-completions format with tool calling. One small client keeps the code simple and makes providers swappable through `LLM_PROVIDER`, so the same eval can compare them.

**2. Guardrails outside the model.**
Some routing rules must never be wrong: outages go to incident management, security issues go to the security team, production write access goes to the cloud team. These are enforced in code after the model answers, and every correction is recorded in the result, so the eval shows how often the model needed correcting.

**3. A labelled eval set before tuning the prompt.**
48 synthetic tickets with the expected category, priority and team. Changes to the prompt or model are judged on the numbers, not on a few hand-picked examples. CI runs the eval on every push.

**4. A keyword baseline as the offline mock.**
CI cannot call a paid or rate-limited API on every push. The mock is a rule-based classifier that speaks the same tool-calling protocol, so the whole agent loop is tested offline. It doubles as a baseline: the LLM has to beat simple keyword rules to justify its cost.

**5. BM25 instead of a vector database.**
With a dozen knowledge-base articles, keyword ranking is accurate, fast and has no infrastructure cost. A vector store becomes worth it with hundreds of articles or many synonyms.

**6. Access through groups, least privilege by default.**
The IAM checker never suggests attaching policies to a user. It recommends the smallest existing group that grants the action and sends deploy, production and admin requests to the cloud team. The Lambda's own role follows the same rule: it can write its own logs, read one SSM parameter and call read-only IAM APIs.

**7. Secrets in SSM Parameter Store, not in Lambda environment variables.**
The API key is a SecureString read once per cold start, so it does not appear in the Lambda console configuration.

**8. SQLite for the demo.**
Zero setup and enough for the demo. On Lambda it lives in `/tmp`, so the triage log resets with each cold start. A production version would use DynamoDB or RDS for a durable log.
