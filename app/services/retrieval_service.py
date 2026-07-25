from __future__ import annotations

from typing import Any

from app.config import settings
from app.retrieve import search


def search_chunks(query: str, top_k: int = 5) -> dict[str, Any]:
    """Thin wrapper over Milestone 2 search(); optionally includes debug timings."""
    timings: dict[str, float] = {}
    hits = search(query, top_k=top_k, timings=timings)
    results = [
        {
            "document": h.document_name,
            "page": h.page,
            "chunk_id": h.chunk_id,
            "distance": h.distance,
            "text": h.text,
        }
        for h in hits
    ]
    payload: dict[str, Any] = {"results": results}
    if settings.debug:
        payload["debug"] = {
            "embedding_time_ms": round(timings.get("embed_ms", 0.0), 1),
            "retrieval_time_ms": round(timings.get("chroma_ms", 0.0), 1),
            "threshold": settings.retrieval_distance_threshold,
            "collection_name": settings.chroma_collection,
        }
    return payload
