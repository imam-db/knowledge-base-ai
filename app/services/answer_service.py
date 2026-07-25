from __future__ import annotations

from typing import Any

from app.answer import answer_question


def ask(question: str, top_k: int = 5) -> dict[str, Any]:
    """Thin wrapper over Milestone 3 answer_question()."""
    return answer_question(question, top_k=top_k)
