from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from rank_bm25 import BM25Okapi

from app.chroma import get_all_chunks, get_chroma_store

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


@dataclass
class KeywordHit:
    chunk_id: str
    rank: int
    score: float
    text: str
    metadata: dict[str, Any]


class KeywordIndex:
    """In-memory BM25 index over Chroma chunk texts."""

    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._chunks: list[dict[str, Any]] = []
        self._version: str | None = None

    def rebuild_if_needed(self, chunks: list[dict[str, Any]] | None = None) -> None:
        version = get_chroma_store().read_version()
        if chunks is not None:
            source = chunks
        else:
            if self._bm25 is not None and self._version == version:
                return
            source = get_all_chunks()

        self._chunks = source
        self._version = version
        if not source:
            self._bm25 = None
            logger.warning("Keyword index empty — no chunks in Chroma")
            return
        corpus = [tokenize(str(c.get("text") or "")) for c in source]
        self._bm25 = BM25Okapi(corpus)
        logger.info("Built BM25 index over %s chunk(s)", len(source))

    def search(self, query: str, top_k: int = 20) -> list[KeywordHit]:
        self.rebuild_if_needed()
        if self._bm25 is None or not self._chunks:
            return []
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        hits: list[KeywordHit] = []
        for rank, (idx, score) in enumerate(ranked[:top_k], start=1):
            chunk = self._chunks[idx]
            hits.append(
                KeywordHit(
                    chunk_id=str(chunk.get("id") or ""),
                    rank=rank,
                    score=float(score),
                    text=str(chunk.get("text") or ""),
                    metadata=dict(chunk.get("metadata") or {}),
                )
            )
        return hits


_default_index: KeywordIndex | None = None


def get_keyword_index() -> KeywordIndex:
    global _default_index
    if _default_index is None:
        _default_index = KeywordIndex()
    return _default_index


def reset_keyword_index() -> None:
    global _default_index
    _default_index = None
