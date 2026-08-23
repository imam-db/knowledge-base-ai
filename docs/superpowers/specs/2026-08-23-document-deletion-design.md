# Milestone 6.5: Document Deletion Design

**Date:** 2026-08-23  
**Status:** Approved  
**Supersedes (partial):** M6 non-goal “Delete from UI” — this milestone adds single-document delete.

## Goal

Allow admins to delete an indexed document from the Documents UI: remove all ChromaDB chunks for that `document_id`, remove the file under `documents/` when present, and refresh the list. Protect delete with the same API key as upload. Do not change ingestion, retrieval, or answer-engine logic.

## Decisions

| Topic | Choice |
|-------|--------|
| Identity | Delete by `document_id` (UUID5 from basename via `make_document_id`) |
| List shape | Extend `DocumentInfo` / `GET /api/v1/documents` with `document_id` so the UI can call DELETE |
| Auth | Same as upload: `X-API-Key` vs `ADMIN_API_KEY` via `require_admin_api_key` |
| Chroma delete | `collection.delete(where={"document_id": document_id})` (same filter as replace) |
| Order | Delete Chroma chunks first, then delete the file on disk |
| Verify chunks | After Chroma delete, re-check that no chunks remain for that id; leftovers → HTTP 500 |
| Missing file | If chunks existed and were deleted but the file is already gone → still HTTP 200 (skip file) |
| File unlink failure | HTTP 500 with clear detail; **do not** roll back Chroma (chunks stay deleted) |
| Orphan file after failed unlink | Known limitation: retry DELETE returns 404 (no chunks). Self-heals on re-upload of the same filename (existing M6 replace). Document in code comments — no id→filename store outside Chroma |
| Not found | Zero chunks for `document_id` → HTTP 404 (`"Document not found"`) |
| Partial Chroma failure | Not fail-soft: HTTP 500 with clear message |
| Confirm UI | `window.confirm` (no styled modal for this milestone) |
| Callback naming | `onDelete` |
| Out of scope | Bulk delete, soft-delete, ingest/retrieve/answer changes, styled confirm modal |

## Architecture

```
Browser (DocumentsPage)
  └─ deleteDocument(documentId) + header X-API-Key from VITE_ADMIN_API_KEY
       │
       ▼
DELETE /api/v1/documents/{document_id}  (Depends: require_admin_api_key)
  └─ documents_service.delete_document(document_id)
        ├─ resolve document_name + chunk_count from Chroma metadata
        ├─ if chunk_count == 0 → raise NotFound
        ├─ chroma.delete_document_chunks(document_id)
        ├─ verify no chunks remain → else raise DeleteError (500)
        └─ unlink documents_dir / document_name if exists
             └─ unlink OSError → raise DeleteError (500); Chroma already deleted
```

## API

### `DELETE /api/v1/documents/{document_id}`

- **Auth:** required (`X-API-Key`)
- **200** — document removed from index (and file removed if it existed)
- **401** — missing/invalid API key (same detail as upload)
- **404** — no chunks for that `document_id`
- **500** — Chroma delete/verify failed, or file unlink failed after successful chunk delete

### Success body — `DeleteResponse`

| Field | Type | Notes |
|-------|------|--------|
| `document_id` | `str` | Path id |
| `document_name` | `str` | Basename from chunk metadata before delete |
| `chunks_deleted` | `int` | Count before delete |
| `status` | `str` | `"deleted"` |

Aligns with `UploadResponse` field naming (`document_id`, `document_name`, `chunks_*`, `status`).

### List change — `DocumentInfo`

| Field | Type | Notes |
|-------|------|--------|
| `document_id` | `str` | **New** — from chunk metadata (same for all chunks of a doc) |
| `name` | `str` | Existing (`document_name`) |
| `pages` | `int` | Existing |
| `uploaded_at` | `str` | Existing |

Grouping stays by `document_name`. Copy `document_id` from chunk metadata (all chunks of a doc share it). If metadata is missing `document_id`, fall back to `make_document_id(name)`.

## Service & Chroma

- Add `delete_document_chunks(document_id)` (or equivalent) in `app/chroma.py` — thin wrapper around `coll.delete(where={"document_id": ...})`. Do **not** misuse `replace_document_chunks` with empty payloads as the public delete API.
- `documents_service.delete_document(document_id) -> dict` raises typed errors mapped by the route:
  - not found → 404
  - delete/unlink failure → 500
- Comment near file-unlink / not-found path: orphan-file limitation + re-upload self-heal (see Known limitation).

## Frontend

- Types: add `document_id` to `DocumentInfo`; add `DeleteResponse`.
- `api.ts`: `deleteDocument(documentId)` using `X-API-Key` from `VITE_ADMIN_API_KEY` (same pattern as `uploadDocument`).
- `DocumentList`: actions column with delete control; before calling parent, `window.confirm` with document name; prop `onDelete(documentId: string)`.
- `DocumentsPage`: handle `onDelete` → call API → on success refresh list; surface errors like upload failures. (Stats refresh is not required unless the page already refreshes stats today.)

## Error mapping

| Condition | HTTP | `detail` (string) |
|-----------|------|-------------------|
| Bad/missing API key | 401 | Existing unauthorized message |
| No chunks for id | 404 | `"Document not found"` |
| Chroma delete or post-delete verify fails | 500 | Clear message (e.g. failed to delete chunks) |
| File unlink fails after chunks deleted | 500 | Clear message (e.g. failed to delete document file); chunks remain deleted |

## Testing

### API (`tests/test_upload_api.py` style or sibling `test_delete_api.py`)

- 401 without / wrong key
- 404 unknown `document_id`
- 200 with `DeleteResponse` body (service mocked)
- service delete error → 500

### Service

- Happy path: chunks removed + file unlinked
- Zero chunks → not found
- File already missing → success after chunk delete
- File unlink fails → error raised **and** assert Chroma chunks already gone (no rollback) — validates orphan / re-upload self-heal story
- List grouping includes `document_id`

### Frontend

- Wiring + confirm is enough; no heavy E2E required for this milestone

## Known limitation

If Chroma delete succeeds and file unlink then fails (500), a second DELETE returns 404 because chunks are gone. The orphan file remains until removed manually or overwritten by uploading the same filename again (existing replace-by-name behavior).

## Non-goals

- Bulk delete
- Soft delete / trash
- Styled confirm modal
- Changes to ingest, retrieve, or answer pipelines
- Persisting id→filename outside Chroma
