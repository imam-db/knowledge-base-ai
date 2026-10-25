from __future__ import annotations

import os
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import uuid4

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings


class ChromaStore:
    """Small wrapper around a persistent Chroma collection."""

    def __init__(
        self,
        collection: Collection | None = None,
        version_path: Path | None = None,
    ) -> None:
        self._collection = collection
        self._client: chromadb.PersistentClient | None = None
        self._collections: dict[str, Collection] = {}
        self._version_path = version_path

    @property
    def version_path(self) -> Path:
        if self._version_path is not None:
            return self._version_path
        return Path(str(settings.chroma_dir) + ".version")

    def bump_version(self) -> None:
        """Atomically write a fresh index version token next to chroma_dir."""
        path = self.version_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=path.name + ".tmp-",
            delete=False,
        ) as handle:
            handle.write(uuid4().hex)
            temp_path = Path(handle.name)
        try:
            os.replace(temp_path, path)
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise

    def read_version(self) -> str:
        """Return the current index version token, or '' when it does not exist."""
        try:
            return self.version_path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return ""

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
        try:
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
        finally:
            self.bump_version()

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
        try:
            coll = collection or self.get_collection()
            coll.delete(where={"document_id": document_id})
        finally:
            self.bump_version()

    def list_documents(self, collection: Collection | None = None) -> list[dict[str, Any]]:
        """Return raw metadatas for every stored chunk (callers aggregate by document)."""
        coll = collection or self.get_collection()
        total = coll.count()
        if total == 0:
            return []
        result = coll.get(include=["metadatas"], limit=total)
        return list(result.get("metadatas") or [])

    def get_all_chunks(
        self,
        collection: Collection | None = None,
    ) -> list[dict[str, Any]]:
        """Return id/text/metadata for every stored chunk."""
        coll = collection or self.get_collection()
        total = coll.count()
        if total == 0:
            return []
        result = coll.get(include=["documents", "metadatas"], limit=total)
        ids = list(result.get("ids") or [])
        documents = list(result.get("documents") or [])
        metadatas = list(result.get("metadatas") or [])
        chunks: list[dict[str, Any]] = []
        for idx, chunk_id in enumerate(ids):
            chunks.append(
                {
                    "id": chunk_id,
                    "text": documents[idx] if idx < len(documents) else "",
                    "metadata": metadatas[idx] if idx < len(metadatas) else {},
                }
            )
        return chunks

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
