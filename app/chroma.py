from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings


def get_collection(name: str | None = None) -> Collection:
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    return client.get_or_create_collection(name=name or settings.chroma_collection)


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
