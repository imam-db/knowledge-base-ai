from __future__ import annotations

from collections.abc import Iterator

from app.core.llm import get_llm_provider


def call_groq(prompt: str) -> str:
    """Send prompt to the configured LLM provider and return raw answer text."""
    return get_llm_provider().generate(prompt)


def stream_groq(prompt: str) -> Iterator[str]:
    return get_llm_provider().generate_stream(prompt)
