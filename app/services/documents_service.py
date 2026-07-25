from __future__ import annotations

from typing import Any

from app.chroma import get_all_metadatas, get_collection


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
        current = grouped.get(name)
        if current is None:
            grouped[name] = {"name": name, "pages": page, "uploaded_at": uploaded_at}
        else:
            if page > current["pages"]:
                current["pages"] = page
            if not current["uploaded_at"] and uploaded_at:
                current["uploaded_at"] = uploaded_at

    documents = sorted(grouped.values(), key=lambda d: d["name"].lower())
    return {"documents": documents}
