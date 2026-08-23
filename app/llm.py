from __future__ import annotations

from app.core.llm import get_llm_provider


def call_groq(prompt: str) -> str:
    """Send prompt to the configured LLM provider and return raw answer text."""
    return get_llm_provider().generate(prompt)
