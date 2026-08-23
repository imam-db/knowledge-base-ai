from __future__ import annotations

from functools import lru_cache
from typing import Sequence

from app.config import ROOT_DIR
from app.retrieve import SearchResult

PROMPTS_DIR = ROOT_DIR / "prompts"


@lru_cache(maxsize=32)
def _read_prompt_file(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def get_system_instructions() -> str:
    return _read_prompt_file("system.txt")


def get_guardrail_message() -> str:
    return _read_prompt_file("not_found.txt")


# Backwards-compatible names used by answer flow and tests.
GUARDRAIL_MESSAGE = get_guardrail_message()


def build_prompt(question: str, chunks: Sequence[SearchResult]) -> str:
    """Build a grounded QA prompt. Does not call LLM or retrieval."""
    parts: list[str] = [get_system_instructions(), "", "Konteks:"]
    for i, chunk in enumerate(chunks, start=1):
        parts.extend(
            [
                "",
                f"[Chunk {i}]",
                f"Document: {chunk.document_name}",
                f"Page: {chunk.page}",
                "Content:",
                chunk.text,
            ]
        )
    parts.extend(["", f"Pertanyaan: {question}", "", "Jawaban:"])
    return "\n".join(parts)
