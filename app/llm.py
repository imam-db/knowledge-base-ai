from __future__ import annotations

from groq import Groq

from app.config import settings


class GroqConfigError(RuntimeError):
    """Raised when GROQ_API_KEY is missing."""


def call_groq(prompt: str) -> str:
    """Send prompt to Groq and return raw answer text. No filtering/citation logic."""
    api_key = settings.groq_api_key
    if not api_key:
        raise GroqConfigError(
            "GROQ_API_KEY is missing. Set it in the environment or .env file."
        )

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return (content or "").strip()
