from __future__ import annotations

from typing import Any, Iterator

from app.answer import answer_question, iter_answer_events


def ask(question: str, top_k: int = 5) -> dict[str, Any]:
    """Thin wrapper over Milestone 3 answer_question()."""
    return answer_question(question, top_k=top_k)


def ask_events(question: str, top_k: int | None = None) -> Iterator[dict[str, Any]]:
    return iter_answer_events(question, top_k=top_k)
