from __future__ import annotations

from pathlib import Path
from typing import Any

from app.chroma import (
    delete_document_chunks,
    get_all_metadatas,
    get_chunks_for_document,
    get_collection,
)
from app.config import make_document_id, settings


class DocumentNotFoundError(Exception):
    """No chunks for document_id in Chroma."""


class DocumentDeleteError(Exception):
    """Chroma verify failed or disk unlink failed after chunk delete."""


def get_stats() -> dict[str, int]:
    coll = get_collection()
    metadatas = get_all_metadatas(coll)
    names = {
        str(meta.get("document_name") or "")
        for meta in metadatas
        if meta and meta.get("document_name")
    }
    return {"documents": len(names), "chunks": coll.count()}


def list_documents() -> dict[str, list[dict[str, Any]]]:
    metadatas = get_all_metadatas()
    grouped: dict[str, dict[str, Any]] = {}
    for meta in metadatas:
        if not meta:
            continue
        name = str(meta.get("document_name") or "").strip()
        if not name:
            continue
        page = int(meta.get("page") or 1)
        uploaded_at = str(meta.get("uploaded_at") or "")
        meta_id = str(meta.get("document_id") or "").strip()
        doc_id = meta_id or make_document_id(name)
        current = grouped.get(name)
        if current is None:
            grouped[name] = {
                "document_id": doc_id,
                "name": name,
                "pages": page,
                "uploaded_at": uploaded_at,
            }
        else:
            if page > current["pages"]:
                current["pages"] = page
            if not current["uploaded_at"] and uploaded_at:
                current["uploaded_at"] = uploaded_at
            if meta_id:
                current["document_id"] = meta_id

    documents = sorted(grouped.values(), key=lambda d: d["name"].lower())
    return {"documents": documents}


def delete_document(document_id: str) -> dict[str, Any]:
    # Known limitation: if unlink fails after chunks are deleted, retry DELETE
    # returns 404; orphan file self-heals on re-upload of the same filename.
    chunks = get_chunks_for_document(document_id)
    if not chunks:
        raise DocumentNotFoundError("Document not found")
    document_name = str(chunks[0].get("document_name") or "").strip()
    if not document_name:
        raise DocumentDeleteError("Document metadata missing document_name")
    document_name = Path(document_name).name
    if not document_name or document_name in {".", ".."}:
        raise DocumentDeleteError("Document metadata missing document_name")
    chunks_deleted = len(chunks)
    try:
        delete_document_chunks(document_id)
    except Exception as exc:
        raise DocumentDeleteError("Failed to delete document chunks") from exc
    remaining = get_chunks_for_document(document_id)
    if remaining:
        raise DocumentDeleteError("Failed to delete document chunks")
    path = settings.documents_dir / document_name
    try:
        path.resolve().relative_to(settings.documents_dir.resolve())
    except ValueError as exc:
        raise DocumentDeleteError("Invalid document path") from exc
    if path.exists():
        try:
            path.unlink()
        except OSError as exc:
            raise DocumentDeleteError("Failed to delete document file") from exc
    return {
        "document_id": document_id,
        "document_name": document_name,
        "chunks_deleted": chunks_deleted,
        "status": "deleted",
    }
