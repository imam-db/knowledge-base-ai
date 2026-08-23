from __future__ import annotations

from typing import Any

from app.chroma import get_all_metadatas, get_collection
from app.config import make_document_id


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
