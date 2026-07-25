from __future__ import annotations

from groq import Groq

from app.config import settings


def call_groq(prompt: str) -> str:
    """Send prompt to Groq and return raw answer text. No filtering/citation logic."""
    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    return (content or "").strip()
