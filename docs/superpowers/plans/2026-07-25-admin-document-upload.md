# Milestone 6: Admin Document Upload Implementation Plan

> **For agentic workers:** Execute task-by-task. Checkbox syntax for tracking.

**Goal:** Sync document upload API + Documents UI, reusing `ingest_file`, UUID5 replace-by-name, API-key protected.

**Architecture:** Thin route → `ingestion_service` (validate, write, rollback) → existing `ingest_file`. Frontend multipart upload with `VITE_ADMIN_API_KEY`.

**Tech Stack:** FastAPI, existing ingest pipeline, React + Vite + Tailwind

**Spec:** `docs/superpowers/specs/2026-07-25-admin-document-upload-design.md`

---

### Task 1: Config + auth dependency + UploadResponse

**Files:**
- Modify: `app/config.py`, `.env.example`, `.env`
- Create: `app/api/deps.py`
- Modify: `app/models/response.py`

- [ ] Add `admin_api_key` + `max_upload_bytes = 20 * 1024 * 1024`
- [ ] `require_admin_api_key` → 401 if missing/wrong
- [ ] `UploadResponse` model

### Task 2: Validation helpers + ingestion_service

**Files:**
- Create: `app/services/ingestion_service.py` (or `app/upload_validation.py` + service)
- Test: `tests/test_ingestion_service.py`, `tests/test_upload_api.py`

- [ ] Magic-byte PDF/DOCX checks; safe basename; size
- [ ] `ingest_uploaded_file(filename, content)` → backup/write/`ingest_file`/rollback
- [ ] Unit tests for validation + mocked ingest

### Task 3: Route POST /api/v1/documents/upload

**Files:**
- Modify: `app/api/routes.py`
- Modify: `tests/test_api.py` or `tests/test_upload_api.py`

### Task 4: Frontend upload

**Files:**
- Modify: `frontend/src/types/index.ts`, `frontend/src/services/api.ts`, `frontend/.env`
- Create: `frontend/src/components/DocumentUpload.tsx`
- Modify: `frontend/src/pages/DocumentsPage.tsx`

### Task 5: E2E manual verification

- Upload, replace, 401, oversized, bad format
