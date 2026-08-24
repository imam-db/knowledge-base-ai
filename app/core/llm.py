from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from groq import Groq

from app.config import settings


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate a completion from a prompt string."""

    def generate_stream(self, prompt: str) -> Iterator[str]:
        """Yield completion text deltas."""


class GroqProvider:
    """Thin Groq chat-completions adapter."""

    def generate(self, prompt: str) -> str:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    def generate_stream(self, prompt: str) -> Iterator[str]:
        client = Groq(api_key=settings.groq_api_key)
        stream = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            stream=True,
        )
        for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            content = getattr(delta, "content", None) if delta is not None else None
            if content:
                yield content


_default_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _default_provider
    if _default_provider is None:
        _default_provider = GroqProvider()
    return _default_provider
