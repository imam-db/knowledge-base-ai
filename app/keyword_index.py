from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from typing import Any

from rank_bm25 import BM25Okapi

from app.core.chroma import ChromaStore, get_chroma_store

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


@dataclass(frozen=True)
class _Snapshot:
    version: str
    bm25: BM25Okapi | None
    chunks: tuple[dict[str, Any], ...]


class KeywordIndex:
    """In-memory BM25 index over Chroma chunk texts."""

    def __init__(self, store: ChromaStore | None = None) -> None:
        self._store = store
        self._snapshot: _Snapshot | None = None
        self._lock = threading.Lock()

    def _current_snapshot(self) -> _Snapshot:
        store = self._store if self._store is not None else get_chroma_store()
        version = store.read_version()
        snap = self._snapshot
        if snap is not None and snap.version == version:
            return snap

        with self._lock:
            version = store.read_version()
            snap = self._snapshot
            if snap is not None and snap.version == version:
                return snap

            chunks = store.get_all_chunks()
            if not chunks:
                bm25 = None
                logger.warning("Keyword index empty — no chunks in Chroma")
            else:
                corpus = [tokenize(str(c.get("text") or "")) for c in chunks]
                bm25 = BM25Okapi(corpus)
                logger.info("Built BM25 index over %s chunk(s)", len(chunks))

            snapshot = _Snapshot(version=version, bm25=bm25, chunks=tuple(chunks))
            self._snapshot = snapshot
            return snapshot

    def rebuild_if_needed(self) -> None:
        self._current_snapshot()

    def search(self, query: str, top_k: int = 20) -> list[KeywordHit]:
        snap = self._current_snapshot()
        if snap.bm25 is None or not snap.chunks:
            return []
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = snap.bm25.get_scores(tokens)
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        hits: list[KeywordHit] = []
        for rank, (idx, score) in enumerate(ranked[:top_k], start=1):
            chunk = snap.chunks[idx]
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
