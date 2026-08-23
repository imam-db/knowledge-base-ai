# Knowledge Application template

Runnable starter for a **Knowledge Application**: ingest documents, retrieve relevant passages, and generate grounded answers with citations.

This repository is the **template baseline** (see ADR-0001). It is template-first: reuse happens by cloning this repo, not by extracting a shared package yet. A Knowledge Application is the product unit; **RAG** is the mechanism inside it.

| Layer | What lives here | Customize per app? |
| ----- | --------------- | ------------------ |
| **Reusable Foundation** | Ingestion, embedding, retrieval, vector store, LLM interface, API, thin UI shell | Rarely — only when proven reusable across ≥2 apps **and** config-only (ADR-0002) |
| **Domain Layer** | `prompts/`, app name / retrieval knobs in `config/config.yaml`, branding | **Yes** — this is where each product gets its character |

Decisions: [`docs/adr/0001-template-first-reuse-strategy.md`](docs/adr/0001-template-first-reuse-strategy.md), [`docs/adr/0002-foundation-and-configuration-boundaries.md`](docs/adr/0002-foundation-and-configuration-boundaries.md), [`docs/adr/0003-template-v1-release-criteria.md`](docs/adr/0003-template-v1-release-criteria.md). Glossary: [`CONTEXT.md`](CONTEXT.md).

## Quick start (clone → secrets → config → run → ingest)

### 1. Clone

```bash
git clone <this-repo-url> my-knowledge-app
cd my-knowledge-app
```

### 2. Secrets (`.env`)

Copy the example and fill API keys. **Secrets stay in `.env` only** — never commit them.

```bash
cp .env.example .env
```

Required:

| Variable | Purpose |
| -------- | ------- |
| `GROQ_API_KEY` | LLM calls for grounded answers |
| `ADMIN_API_KEY` | Protects document upload/delete (`X-API-Key`) |

Optional: `CONFIG_PATH` if you keep config outside `config/config.yaml`.

### 3. Application config (`config/config.yaml`)

Edit display name, models, chunking, retrieval threshold, paths, and collection name. Defaults are already sensible for a neutral Indonesian template.

```yaml
app:
  name: My Clinic Assistant   # shown in API / UI branding target
```

Prompt behaviour is **not** in yaml — edit Domain Layer files under `prompts/` (see below).

### 4. Install and run backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/api/v1/health`

### 5. Install and run frontend (optional)

```bash
cd frontend
npm install
# Optional: create frontend/.env with VITE_ADMIN_API_KEY matching ADMIN_API_KEY
npm run dev
```

UI defaults to `http://localhost:8000/api/v1`. Override with `VITE_API_URL` if needed.

### 6. Add documents and ingest

- Place PDF/DOCX under `documents/` (runtime uploads; this folder is gitignored except `documents/samples/`).
- Or upload via the Documents UI / `POST /api/v1/documents/upload` with `X-API-Key`.

CLI ingest (indexes everything currently in the documents directory):

```bash
python -m app.ingest
```

Then ask questions via the Chat UI or `POST /api/v1/ask`.

## Domain Layer customization

After clone, typically change:

1. **`config/config.yaml`** — `app.name`, retrieval threshold, models, collection name  
2. **`prompts/system.txt`** — persona and grounding rules (neutral Indonesian by default)  
3. **`prompts/not_found.txt`** — exact guardrail when context is insufficient  
4. **Frontend chrome** — title/heading if you want stronger product branding  

Do **not** put company persona or business rules into Foundation modules under `app/core/` unless they pass the ADR-0002 filter (proven reuse + config-only).

## Layout

```text
├── app/                 # FastAPI app + RAG pipeline
│   └── core/            # Thin LLM / embedding / Chroma interfaces
├── config/config.yaml   # Application parameters (not secrets)
├── prompts/             # Domain Layer prompt files
├── frontend/            # Chat + documents UI shell
├── documents/           # Runtime corpus (gitignored); samples/ optional
├── chroma_db/           # Generated vector store (gitignored)
├── tests/
├── docs/adr/
├── .env.example
└── CONTEXT.md
```

## What not to commit

- `.env` and API keys  
- `chroma_db/` (rebuild with ingest)  
- Runtime files under `documents/` (use `documents/samples/` only for intentional demo fixtures)

## Tests

```bash
pytest
```

## License / origin

This baseline grew out of a Knowledge Base AI product implementation. Git history may still reflect that origin; product #1 is intended to live in a separate forked repo after the `template-v1` tag (ADR-0001 / ADR-0003).
