from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings

_client: chromadb.PersistentClient | None = None
_collections: dict[str, Collection] = {}


def get_collection(name: str | None = None) -> Collection:
    """Return a cached PersistentClient collection (initialized once at startup)."""
    global _client
    collection_name = name or settings.chroma_collection
    if collection_name in _collections:
        return _collections[collection_name]
    if _client is None:
        _client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    coll = _client.get_or_create_collection(name=collection_name)
    _collections[collection_name] = coll
    return coll


def get_all_metadatas(collection: Collection | None = None) -> list[dict[str, Any]]:
    """Fetch metadatas for every item in the collection."""
    coll = collection or get_collection()
    total = coll.count()
    if total == 0:
        return []
    result = coll.get(include=["metadatas"], limit=total)
    return list(result.get("metadatas") or [])


def get_chunks_for_document(
    document_id: str,
    collection: Collection | None = None,
) -> list[dict[str, Any]]:
    coll = collection or get_collection()
    result = coll.get(
        where={"document_id": document_id},
        include=["metadatas"],
    )
    return [m for m in (result.get("metadatas") or []) if m]


def delete_document_chunks(
    document_id: str,
    collection: Collection | None = None,
) -> None:
    coll = collection or get_collection()
    coll.delete(where={"document_id": document_id})


def replace_document_chunks(
    *,
    document_id: str,
    texts: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    metadatas: Sequence[dict[str, Any]],
    ids: Sequence[str],
    collection: Collection | None = None,
) -> None:
    coll = collection or get_collection()
    coll.delete(where={"document_id": document_id})
    if not texts:
        return
    coll.add(
        documents=list(texts),
        embeddings=list(embeddings),
        metadatas=list(metadatas),
        ids=list(ids),
    )


def query_similar(
    query_embedding: Sequence[float],
    n_results: int = 5,
    collection: Collection | None = None,
) -> dict[str, Any]:
    """Query collection by embedding. Returns Chroma query result dict for one query."""
    coll = collection or get_collection()
    if coll.count() == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    return coll.query(
        query_embeddings=[list(query_embedding)],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
