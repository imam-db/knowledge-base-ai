from __future__ import annotations

from typing import Sequence

from app.retrieve import SearchResult

SYSTEM_INSTRUCTIONS = """Anda adalah asisten knowledge base perusahaan.
Jawab HANYA berdasarkan konteks dokumen yang diberikan di bawah.
Jika konteks tidak cukup untuk menjawab, balas persis:
Maaf, informasi tersebut tidak ditemukan pada dokumen yang tersedia.
Jangan menggunakan pengetahuan umum di luar konteks.
Jangan menambahkan daftar sumber, sitasi, atau rujukan dokumen — sistem akan menampilkannya terpisah.
"""

GUARDRAIL_MESSAGE = (
    "Maaf, informasi tersebut tidak ditemukan pada dokumen yang tersedia."
)


def build_prompt(question: str, chunks: Sequence[SearchResult]) -> str:
    """Build a grounded QA prompt. Does not call LLM or retrieval."""
    parts: list[str] = [SYSTEM_INSTRUCTIONS.strip(), "", "Konteks:"]
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
