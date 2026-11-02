# CloudDesk AI

An LLM-powered service-desk agent for IT and cloud support tickets.

CloudDesk AI reads a support ticket, classifies it by category and priority, uses tools to investigate (a knowledge-base search, SQL lookups on users and ticket history, and an AWS IAM access check), drafts a reply for the user and decides whether to escalate to a human engineer.

> Status: in development.

## Why

I worked for two years on an IT service desk, handling 40+ tickets a day in ServiceNow across Active Directory, Microsoft 365 and access requests. Most of the first diagnosis step follows the same pattern every time: read the ticket, check the user's account, look up the known fix, decide who owns it. This project automates that first step with an LLM agent and measures how accurate it is.

## Built with

Python, SQL (SQLite), an OpenAI-compatible LLM API (Groq, Gemini or local Ollama), developed with Claude Code as an AI pair programmer.
