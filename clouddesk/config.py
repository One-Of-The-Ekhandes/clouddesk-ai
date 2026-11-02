"""Runtime settings, read from environment variables (and a local .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# OpenAI-compatible chat endpoints. Groq, Gemini and Ollama all expose one,
# so a single client works for every provider.
PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "GROQ_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.5-flash", "GEMINI_API_KEY"),
    "ollama": (os.getenv("OLLAMA_URL", "http://localhost:11434/v1"), "llama3.2", None),
}


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    base_url: str
    api_key: str | None
    db_path: Path
    kb_dir: Path
    iam_source: str
    iam_snapshot: Path


def get_settings() -> Settings:
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if not provider:  # pick the first provider that has a key, else run offline
        provider = "groq" if os.getenv("GROQ_API_KEY") else "gemini" if os.getenv("GEMINI_API_KEY") else "mock"
    if provider not in PROVIDERS and provider != "mock":
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Use groq, gemini, ollama or mock.")
    base_url, default_model, key_var = PROVIDERS.get(provider, ("", "mock", None))
    return Settings(
        provider=provider,
        model=os.getenv("LLM_MODEL", default_model),
        base_url=base_url,
        api_key=os.getenv(key_var) if key_var else None,
        db_path=Path(os.getenv("CLOUDDESK_DB", ROOT / "clouddesk.db")),
        kb_dir=ROOT / "data" / "kb",
        iam_source=os.getenv("IAM_SOURCE", "snapshot").strip().lower(),
        iam_snapshot=ROOT / "data" / "iam_snapshot.json",
    )
