# Knowledge Base AI

**Knowledge Application** product #1 for internal company SOP / policy / FAQ.

Forked from [`knowledge-application-template`](https://github.com/imam-db/knowledge-application-template) at tag `template-v1`. The Reusable Foundation stays aligned with that template; this repo owns the **Domain Layer** (prompts, product name, branding).

## Setup

```bash
git clone https://github.com/imam-db/knowledge-base-ai.git
cd knowledge-base-ai
cp .env.example .env   # set GROQ_API_KEY and ADMIN_API_KEY
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Optional frontend:

```bash
cd frontend && npm install && npm run dev
```

Backend:

```bash
uvicorn app.main:app --reload --port 8000
```

## Re-ingest (required after clone)

This repo does **not** ship `.env`, `chroma_db/`, or runtime documents. After clone:

1. Put PDF/DOCX under `documents/` (or upload via the Documents UI with `X-API-Key`).
2. Rebuild the vector store:

```bash
python -m app.ingest
```

Or use `POST /api/v1/documents/upload` — upload runs ingest for that file.

## Domain Layer

| Path | Role |
| ---- | ---- |
| `config/config.yaml` | `app.name: Knowledge Base AI` and deployment knobs |
| `prompts/system.txt` | Company knowledge-base persona |
| `prompts/not_found.txt` | Guardrail when context is insufficient |
| `frontend/` | Product chrome |

Foundation code under `app/core/` should not absorb business rules unless they pass ADR-0002 (proven reuse + config-only).

## Template upstream

Important Foundation fixes are ported manually from `knowledge-application-template` until a later `rag-core` package exists. No automatic sync.

## Tests

```bash
pytest
```
