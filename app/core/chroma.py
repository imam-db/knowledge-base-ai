from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings


class ChromaStore:
    """Small wrapper around a persistent Chroma collection."""

    def __init__(self, collection: Collection | None = None) -> None:
        self._collection = collection
        self._client: chromadb.PersistentClient | None = None
        self._collections: dict[str, Collection] = {}

    def get_collection(self, name: str | None = None) -> Collection:
        if self._collection is not None and name is None:
            return self._collection
        collection_name = name or settings.chroma_collection
        if collection_name in self._collections:
            return self._collections[collection_name]
        if self._client is None:
            self._client = chromadb.PersistentClient(path=str(settings.chroma_dir))
        coll = self._client.get_or_create_collection(name=collection_name)
        self._collections[collection_name] = coll
        return coll

    def add(
        self,
        *,
        document_id: str,
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float]],
        metadatas: Sequence[dict[str, Any]],
        ids: Sequence[str],
        collection: Collection | None = None,
    ) -> None:
        """Replace all chunks for a document_id, then add the new set."""
        coll = collection or self.get_collection()
        coll.delete(where={"document_id": document_id})
        if not texts:
            return
        coll.add(
            documents=list(texts),
            embeddings=list(embeddings),
            metadatas=list(metadatas),
            ids=list(ids),
        )

    def search(
        self,
        query_embedding: Sequence[float],
        n_results: int = 5,
        collection: Collection | None = None,
    ) -> dict[str, Any]:
        coll = collection or self.get_collection()
        if coll.count() == 0:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        return coll.query(
            query_embeddings=[list(query_embedding)],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

    def delete(self, document_id: str, collection: Collection | None = None) -> None:
        coll = collection or self.get_collection()
        coll.delete(where={"document_id": document_id})

    def list_documents(self, collection: Collection | None = None) -> list[dict[str, Any]]:
        """Return raw metadatas for every stored chunk (callers aggregate by document)."""
        coll = collection or self.get_collection()
        total = coll.count()
        if total == 0:
            return []
        result = coll.get(include=["metadatas"], limit=total)
        return list(result.get("metadatas") or [])

    def get_chunks_for_document(
        self,
        document_id: str,
        collection: Collection | None = None,
    ) -> list[dict[str, Any]]:
        coll = collection or self.get_collection()
        result = coll.get(
            where={"document_id": document_id},
            include=["metadatas"],
        )
        return [m for m in (result.get("metadatas") or []) if m]


_default_store: ChromaStore | None = None


def get_chroma_store() -> ChromaStore:
    global _default_store
    if _default_store is None:
        _default_store = ChromaStore()
    return _default_store
