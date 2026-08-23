# Milestone 6.5: Document Deletion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add admin `DELETE /api/v1/documents/{document_id}` (Chroma chunks then disk file) and a confirm+delete control on the Documents UI list.

**Architecture:** Thin route → `documents_service.delete_document` → `chroma.delete_document_chunks` + verify + unlink. Extend list payload with `document_id`. Same `X-API-Key` auth as upload. No ingest/retrieve/answer changes.

**Tech Stack:** FastAPI, ChromaDB, React + Vite + Tailwind (existing Documents page)

**Spec:** `docs/superpowers/specs/2026-08-23-document-deletion-design.md`

---

## File map

| File | Responsibility |
|------|----------------|
| `app/models/response.py` | `DeleteResponse`; add `document_id` to `DocumentInfo` |
| `app/chroma.py` | `delete_document_chunks(document_id)`; helper to fetch metadatas by id |
| `app/services/documents_service.py` | Include `document_id` in list; `delete_document`; typed errors |
| `app/api/routes.py` | `DELETE /api/v1/documents/{document_id}` |
| `tests/test_documents_service.py` | List `document_id` + delete service tests |
| `tests/test_api.py` | Update `test_documents_list` mock payload for required `document_id` |
| `tests/test_delete_api.py` | Route auth / 404 / 200 / 500 |
| `frontend/src/types/index.ts` | Types |
| `frontend/src/services/api.ts` | `deleteDocument` |
| `frontend/src/components/DocumentList.tsx` | Delete button + `window.confirm` + `onDelete` |
| `frontend/src/pages/DocumentsPage.tsx` | Wire delete + refresh list + error UX |

---

### Task 1: Response models + list `document_id`

**Files:**
- Modify: `app/models/response.py`
- Modify: `app/services/documents_service.py`
- Modify: `tests/test_documents_service.py`
- Modify: `tests/test_api.py` (`test_documents_list`)

- [ ] **Step 1: Write failing list test for `document_id`**

Update `test_list_documents_groups_max_page_and_uploaded_at` (and/or add a focused test) so expected rows include `document_id` from metadata, with fallback via `make_document_id(name)` when metadata omits it:

```python
def test_list_documents_includes_document_id():
    metadatas = [
        {
            "document_id": "11111111-1111-5111-8111-111111111111",
            "document_name": "SOP.pdf",
            "page": 1,
            "uploaded_at": "2026-07-25",
        },
        {
            "document_id": "11111111-1111-5111-8111-111111111111",
            "document_name": "SOP.pdf",
            "page": 4,
            "uploaded_at": "2026-07-25",
        },
        {
            "document_name": "FAQ.docx",
            "page": 1,
            "uploaded_at": "2026-07-24",
        },
    ]
    from app.config import make_document_id

    with patch("app.services.documents_service.get_all_metadatas", return_value=metadatas):
        result = list_documents()
    assert result["documents"] == [
        {
            "document_id": make_document_id("FAQ.docx"),
            "name": "FAQ.docx",
            "pages": 1,
            "uploaded_at": "2026-07-24",
        },
        {
            "document_id": "11111111-1111-5111-8111-111111111111",
            "name": "SOP.pdf",
            "pages": 4,
            "uploaded_at": "2026-07-25",
        },
    ]
```

Also update `test_list_documents_groups_max_page_and_uploaded_at` expectations to include `document_id` (use `make_document_id` for names without id in fixtures).

Update `tests/test_api.py::test_documents_list` mock payload so response validation still passes once `DocumentInfo.document_id` is required:

```python
def test_documents_list():
    payload = {
        "documents": [
            {
                "document_id": "11111111-1111-5111-8111-111111111111",
                "name": "sample_faq.docx",
                "pages": 1,
                "uploaded_at": "2026-07-25",
            },
        ]
    }
    with patch("app.api.routes.documents_service.list_documents", return_value=payload):
        res = client.get("/api/v1/documents")
    assert res.status_code == 200
    assert res.json()["documents"][0]["name"] == "sample_faq.docx"
    assert res.json()["documents"][0]["pages"] == 1
    assert res.json()["documents"][0]["document_id"] == "11111111-1111-5111-8111-111111111111"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_documents_service.py::test_list_documents_includes_document_id -v`  
Expected: FAIL (missing `document_id` key / assertion)

- [ ] **Step 3: Implement models + list grouping**

In `app/models/response.py`:

```python
class DocumentInfo(BaseModel):
    document_id: str
    name: str
    pages: int
    uploaded_at: str


class DeleteResponse(BaseModel):
    document_id: str
    document_name: str
    chunks_deleted: int
    status: str
```

In `list_documents`, when creating/updating a group (key = `document_name`):

```python
from app.config import make_document_id

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
    # Prefer an explicit metadata document_id over a fallback-computed one
    if meta_id:
        current["document_id"] = meta_id
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_documents_service.py tests/test_api.py::test_documents_list -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/models/response.py app/services/documents_service.py tests/test_documents_service.py tests/test_api.py
git commit -m "feat: include document_id in documents list response"
```

---

### Task 2: Chroma delete helper + service `delete_document`

**Files:**
- Modify: `app/chroma.py`
- Modify: `app/services/documents_service.py`
- Modify: `tests/test_documents_service.py`

- [ ] **Step 1: Write failing service tests**

Add to `tests/test_documents_service.py`:

```python
import pytest
from pathlib import Path
from app.services.documents_service import (
    DocumentDeleteError,
    DocumentNotFoundError,
    delete_document,
)


def test_delete_document_not_found():
    with patch(
        "app.services.documents_service.get_chunks_for_document",
        return_value=[],
    ):
        with pytest.raises(DocumentNotFoundError):
            delete_document("missing-id")


def test_delete_document_happy_path(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.documents_service.settings.documents_dir",
        tmp_path,
    )
    path = tmp_path / "a.pdf"
    path.write_bytes(b"%PDF")
    metas = [
        {"document_id": "id-1", "document_name": "a.pdf"},
        {"document_id": "id-1", "document_name": "a.pdf"},
    ]
    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, []],
        ),
        patch("app.services.documents_service.delete_document_chunks") as del_chunks,
    ):
        result = delete_document("id-1")
    del_chunks.assert_called_once_with("id-1")
    assert result == {
        "document_id": "id-1",
        "document_name": "a.pdf",
        "chunks_deleted": 2,
        "status": "deleted",
    }
    assert not path.exists()


def test_delete_document_missing_file_still_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.documents_service.settings.documents_dir",
        tmp_path,
    )
    metas = [{"document_id": "id-1", "document_name": "gone.pdf"}]
    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, []],
        ),
        patch("app.services.documents_service.delete_document_chunks"),
    ):
        result = delete_document("id-1")
    assert result["status"] == "deleted"
    assert result["chunks_deleted"] == 1


def test_delete_document_unlink_failure_does_not_rollback_chunks(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "app.services.documents_service.settings.documents_dir",
        tmp_path,
    )
    path = tmp_path / "a.pdf"
    path.write_bytes(b"%PDF")
    metas = [{"document_id": "id-1", "document_name": "a.pdf"}]
    real_unlink = Path.unlink

    def boom(self, *args, **kwargs):
        if self == path:
            raise OSError("permission denied")
        return real_unlink(self, *args, **kwargs)

    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, []],
        ),
        patch("app.services.documents_service.delete_document_chunks") as del_chunks,
        patch.object(Path, "unlink", boom),
    ):
        with pytest.raises(DocumentDeleteError, match="file"):
            delete_document("id-1")
    del_chunks.assert_called_once_with("id-1")
    # chunks already deleted — no rollback API called
```

Add a verify-failure test:

```python
def test_delete_document_verify_chunks_remain_raises():
    metas = [{"document_id": "id-1", "document_name": "a.pdf"}]
    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, metas],  # still present after delete
        ),
        patch("app.services.documents_service.delete_document_chunks"),
    ):
        with pytest.raises(DocumentDeleteError, match="chunks"):
            delete_document("id-1")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_documents_service.py -k delete_document -v`  
Expected: FAIL (import / function missing)

- [ ] **Step 3: Implement chroma helpers + service**

In `app/chroma.py`:

```python
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
```

In `app/services/documents_service.py`:

```python
class DocumentNotFoundError(Exception):
    """No chunks for document_id in Chroma."""


class DocumentDeleteError(Exception):
    """Chroma verify failed or disk unlink failed after chunk delete."""


def delete_document(document_id: str) -> dict[str, Any]:
    # Known limitation: if unlink fails after chunks are deleted, retry DELETE
    # returns 404; orphan file self-heals on re-upload of the same filename.
    chunks = get_chunks_for_document(document_id)
    if not chunks:
        raise DocumentNotFoundError("Document not found")
    document_name = str(chunks[0].get("document_name") or "").strip()
    if not document_name:
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
```

Import `get_chunks_for_document` / `delete_document_chunks` from `app.chroma` (re-export or import in service — prefer importing from chroma in the service module; tests patch `app.services.documents_service.*`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_documents_service.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/chroma.py app/services/documents_service.py tests/test_documents_service.py
git commit -m "feat: delete document chunks from Chroma and remove file"
```

---

### Task 3: DELETE API route

**Files:**
- Create: `tests/test_delete_api.py`
- Modify: `app/api/routes.py`

- [ ] **Step 1: Write failing API tests**

```python
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

with (
    patch("app.main.get_model"),
    patch("app.main.get_collection"),
):
    from app.main import app

client = TestClient(app)


def test_delete_requires_api_key(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    res = client.delete("/api/v1/documents/some-id")
    assert res.status_code == 401


def test_delete_rejects_wrong_api_key(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    res = client.delete(
        "/api/v1/documents/some-id",
        headers={"X-API-Key": "wrong"},
    )
    assert res.status_code == 401


def test_delete_not_found(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    from app.services.documents_service import DocumentNotFoundError

    with patch(
        "app.api.routes.documents_service.delete_document",
        side_effect=DocumentNotFoundError("Document not found"),
    ):
        res = client.delete(
            "/api/v1/documents/missing",
            headers={"X-API-Key": "secret-key"},
        )
    assert res.status_code == 404
    assert res.json()["detail"] == "Document not found"


def test_delete_success(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    payload = {
        "document_id": "id-1",
        "document_name": "a.pdf",
        "chunks_deleted": 3,
        "status": "deleted",
    }
    with patch(
        "app.api.routes.documents_service.delete_document",
        return_value=payload,
    ) as mocked:
        res = client.delete(
            "/api/v1/documents/id-1",
            headers={"X-API-Key": "secret-key"},
        )
    assert res.status_code == 200
    assert res.json() == payload
    mocked.assert_called_once_with("id-1")


def test_delete_maps_delete_error_to_500(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    from app.services.documents_service import DocumentDeleteError

    with patch(
        "app.api.routes.documents_service.delete_document",
        side_effect=DocumentDeleteError("Failed to delete document file"),
    ):
        res = client.delete(
            "/api/v1/documents/id-1",
            headers={"X-API-Key": "secret-key"},
        )
    assert res.status_code == 500
    assert res.json()["detail"] == "Failed to delete document file"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_delete_api.py -v`  
Expected: FAIL (404 from FastAPI — route missing — or similar)

- [ ] **Step 3: Implement route**

In `app/api/routes.py`, import `DeleteResponse`, `DocumentDeleteError`, `DocumentNotFoundError`, and add:

```python
@router.delete(
    "/api/v1/documents/{document_id}",
    response_model=DeleteResponse,
    summary="Delete an indexed document",
    description=(
        "Deletes all Chroma chunks for document_id, then removes the file under "
        "documents/ if present. Requires X-API-Key."
    ),
)
async def delete_document(
    document_id: str,
    _: None = Depends(require_admin_api_key),
) -> DeleteResponse:
    try:
        result = documents_service.delete_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentDeleteError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return DeleteResponse(**result)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_delete_api.py tests/test_documents_service.py tests/test_upload_api.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/routes.py tests/test_delete_api.py
git commit -m "feat: add DELETE /api/v1/documents/{document_id} endpoint"
```

---

### Task 4: Frontend delete UI

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/components/DocumentList.tsx`
- Modify: `frontend/src/pages/DocumentsPage.tsx`

- [ ] **Step 1: Types + API client**

```typescript
export interface DocumentInfo {
  document_id: string
  name: string
  pages: number
  uploaded_at: string
}

export interface DeleteResponse {
  document_id: string
  document_name: string
  chunks_deleted: number
  status: string
}
```

```typescript
export async function deleteDocument(documentId: string): Promise<DeleteResponse> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  const apiKey = import.meta.env.VITE_ADMIN_API_KEY as string | undefined
  if (apiKey) headers['X-API-Key'] = apiKey

  const response = await fetch(
    `${API_URL}/documents/${encodeURIComponent(documentId)}`,
    { method: 'DELETE', headers },
  )
  if (!response.ok) {
    throw new Error(await readErrorDetail(response))
  }
  return response.json() as Promise<DeleteResponse>
}
```

- [ ] **Step 2: DocumentList delete control**

- Add prop `onDelete: (documentId: string) => void` (and optional `deletingId?: string | null` if useful).
- Add Actions column with a button (text “Hapus” or a simple trash SVG matching existing ink/danger tokens).
- On click: `if (!window.confirm(\`Hapus ${doc.name}? Chunk dan file akan dihapus.\`)) return;` then `onDelete(doc.document_id)`.
- Use `key={doc.document_id}` instead of `doc.name`.

- [ ] **Step 3: DocumentsPage wiring**

- Import `deleteDocument`.
- State: `deleteError: string | null` (mirror `uploadError`).
- Handler (mirror upload):

```typescript
const handleDelete = async (documentId: string) => {
  setDeleteError(null)
  setSuccess(null)
  try {
    const result = await deleteDocument(documentId)
    await refreshDocuments()
    setSuccess(`Berhasil menghapus ${result.document_name} (${result.chunks_deleted} chunk).`)
  } catch (err) {
    setDeleteError(err instanceof Error ? err.message : 'Hapus gagal')
  }
}
```

- Pass `onDelete={(id) => void handleDelete(id)}` to `DocumentList`.
- Show `deleteError` banner similar to `uploadError`.

- [ ] **Step 4: Manual smoke**

With backend running and `VITE_ADMIN_API_KEY` set:

1. Open Documents page — list shows documents.
2. Cancel confirm → no DELETE request.
3. Confirm delete → row gone after refresh; API 200.
4. Wrong/missing key → 401 surfaced as error.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/services/api.ts frontend/src/components/DocumentList.tsx frontend/src/pages/DocumentsPage.tsx
git commit -m "feat: add document delete control on Documents page"
```

---

### Task 5: Final verification

- [ ] **Step 1: Run full relevant pytest**

Run: `pytest tests/test_documents_service.py tests/test_delete_api.py tests/test_upload_api.py tests/test_api.py -v`  
Expected: all PASS (especially `test_documents_list` with `document_id`)

- [ ] **Step 2: Optional typecheck frontend**

Run: `cd frontend && npx tsc --noEmit`  
Expected: no errors

- [ ] **Step 3: Done** — no further commit unless fixes were needed
