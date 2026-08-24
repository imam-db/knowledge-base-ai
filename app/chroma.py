from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from chromadb.api.models.Collection import Collection

from app.core.chroma import get_chroma_store


def get_collection(name: str | None = None) -> Collection:
    """Return a cached PersistentClient collection (initialized once at startup)."""
    return get_chroma_store().get_collection(name)


def get_all_metadatas(collection: Collection | None = None) -> list[dict[str, Any]]:
    """Fetch metadatas for every item in the collection."""
    return get_chroma_store().list_documents(collection)


def get_chunks_for_document(
    document_id: str,
    collection: Collection | None = None,
) -> list[dict[str, Any]]:
    return get_chroma_store().get_chunks_for_document(document_id, collection)


def delete_document_chunks(
    document_id: str,
    collection: Collection | None = None,
) -> None:
    get_chroma_store().delete(document_id, collection)


def replace_document_chunks(
    *,
    document_id: str,
    texts: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    metadatas: Sequence[dict[str, Any]],
    ids: Sequence[str],
    collection: Collection | None = None,
) -> None:
    get_chroma_store().add(
        document_id=document_id,
        texts=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
        collection=collection,
    )


def query_similar(
    query_embedding: Sequence[float],
    n_results: int = 5,
    collection: Collection | None = None,
) -> dict[str, Any]:
    """Query collection by embedding. Returns Chroma query result dict for one query."""
    return get_chroma_store().search(query_embedding, n_results=n_results, collection=collection)


def get_all_chunks(collection: Collection | None = None) -> list[dict[str, Any]]:
    return get_chroma_store().get_all_chunks(collection)
