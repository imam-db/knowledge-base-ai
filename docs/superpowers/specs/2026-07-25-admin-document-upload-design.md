# Milestone 6: Admin & Document Management Design

**Date:** 2026-07-25  
**Status:** Approved

## Goal

Allow admins to upload `.pdf` / `.docx` from the Documents UI, run the existing sync ingestion pipeline for that file only, and have the document immediately available for chat retrieval. Protect upload with a simple API key. Do not change the M1 `document_id` scheme.

## Decisions

| Topic | Choice |
|-------|--------|
| Ingestion style | Sync request/response (no queue/async for M6) |
| Pipeline reuse | Call existing `ingest_file(path)` via thin service; no duplicated chunk/embed logic in routes |
| `document_id` | Unchanged: `uuid.uuid5(NAMESPACE_URL, basename)` via `make_document_id` |
| Same filename | Replace prior vectors + overwrite file on disk (M1 replace-by-name) |
| MIME validation | Magic bytes only (no new deps): PDF starts with `%PDF`; DOCX is ZIP (`PK`) containing `word/` |
| Max size | 20MB; larger → HTTP 400 |
| Empty / no chunks | HTTP 400 `"Document produced no usable content"`; remove the newly written file (restore previous file bytes if this was a replace) |
| Filename | Light sanitize: basename only; reject `..` and path separators; keep original display name otherwise |
| Auth | `X-API-Key` vs `ADMIN_API_KEY` **only** on `POST /api/v1/documents/upload`; other endpoints stay open |
| READY status | Implicit: HTTP 200 means ingested and retrievable; no separate status store |
| Out of scope | Delete from UI, re-index button, background jobs, login form |

## Architecture

```
Browser (DocumentsPage)
  └─ uploadDocument(file) + header X-API-Key from VITE_ADMIN_API_KEY
       │
       ▼
POST /api/v1/documents/upload  (Depends: require_admin_api_key)
  └─ validate size / extension / magic bytes / safe basename
  └─ IngestionService.ingest_upload(filename, bytes)
        ├─ backup existing documents/{name} if present
        ├─ write documents/{name}
        ├─ ingest_file(path)   # existing M1 pipeline
        └─ on failure: restore backup or delete new file; raise typed error
```

Route handlers stay thin. Parsing, chunking, embedding, and Chroma replace remain inside `app/ingest.py` / loaders / chroma.

## Backend

### Config

Add to `Settings` / `.env` / `.env.example`:

- `ADMIN_API_KEY` (required for upload; empty key means all upload attempts get 401)

### Auth dependency

`require_admin_api_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None)`:

- Missing/wrong/empty configured key → `HTTPException(401, detail="Unauthorized: invalid or missing API key")`
- Applied only on the upload route via `Depends`

### Endpoint

`POST /api/v1/documents/upload`

- Multipart field: `file` (`UploadFile`)
- Success **200**:

```json
{
  "document_id": "<uuid5>",
  "document_name": "sample_faq.docx",
  "chunks_created": 1,
  "status": "ready"
}
```

- Validation / empty content / load errors → **400** with clear `detail` string (e.g. `"File too large (max 20MB)"`, `"Unsupported document"`, `"Unsupported file type"`, `"Document produced no usable content"`, `"Invalid file name"`)
- Auth failure → **401**
- Unexpected embed/Chroma failure → **500** (and attempt file rollback)

### Service layer

`app/services/ingestion_service.py` (name may be `IngestionService` functions style matching existing services):

- `ingest_uploaded_file(*, filename: str, content: bytes) -> dict`
- Uses `make_document_id`, writes under `settings.documents_dir`, calls `ingest_file`
- Maps `IngestLoadError` / zero chunks → domain error consumed by route as 400
- Does **not** call `run_ingest()` / full-folder discover

### Helpers

- `app/api/deps.py` — API key dependency
- Small validator module or functions in service: size, suffix, magic-byte sniff, safe basename

### Response model

`UploadResponse` in `app/models/response.py` with fields above.

## Frontend

### `services/api.ts`

- `uploadDocument(file: File): Promise<UploadResponse>`
- `FormData` + `file` field; set `X-API-Key` from `import.meta.env.VITE_ADMIN_API_KEY`
- Do **not** force `Content-Type: application/json` on this call (browser sets multipart boundary)

### Types

`UploadResponse` mirroring backend.

### UI (`DocumentsPage` + small `DocumentUpload` component)

- Drag-and-drop zone and/or file picker; accept `.pdf,.docx`
- While uploading: clear loading copy **“Memproses dokumen…”** (disable further submits)
- Success: short success banner + re-fetch `GET /documents`
- Error: show human-readable message from API `detail` (400/401/500), not raw JSON
- Env: `VITE_ADMIN_API_KEY` in `frontend/.env` (demo only; no login form)

`DocumentsPage` continues to own its list fetch state (not lifted to `App`).

## Testing (acceptance)

1. Upload new PDF/DOCX via UI → appears in Documents list → answerable in Chat  
2. Re-upload same filename → still one document in list (replace, not duplicate); content reflects new file  
3. Upload without / wrong API key → 401  
4. Oversized file → 400 clear message  
5. Wrong format / spoofed extension → 400 `"Unsupported document"` or type message  

## Non-goals

- Async/queue workers  
- Per-document READY enum in DB  
- Delete / bulk re-ingest from UI  
- Production auth (OAuth, roles)
