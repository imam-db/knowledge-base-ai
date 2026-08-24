# Knowledge Base AI

**Knowledge Application** product #1 — portfolio demo (Premier League handbook RAG) and optional playground deploy.

Forked from [`knowledge-application-template`](https://github.com/imam-db/knowledge-application-template) at tag `template-v1`. The Reusable Foundation stays aligned with that template; this repo owns the **Domain Layer** (prompts, product name, branding).

## Deploy modes

Two public surfaces from **one codebase**, different config per subdomain:

| Target | Config | UX |
| ------ | ------ | -- |
| `kb.vvizh.com` (portfolio) | `config/config.yaml` | Chat-only, preloaded handbook |
| `kb-playground.vvizh.com` | `config/config.playground.yaml` | Upload + chat, optional sample docs |

Set `CONFIG_PATH` when starting the API:

```bash
# Portfolio (default)
uvicorn app.main:app --reload --port 8000

# Playground
CONFIG_PATH=config/config.playground.yaml uvicorn app.main:app --reload --port 8001
```

UI mode is exposed at `GET /api/v1/config` — the frontend reads `ui.mode`, `show_documents`, subtitle, and example questions from there.

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

1. Put the Premier League handbook PDF under `documents/` (portfolio) or your corpus files.
2. Rebuild the vector store:

```bash
python -m app.ingest
```

Playground mode also supports `POST /api/v1/documents/upload` with `X-API-Key`. Portfolio deploy typically ingests at build/deploy time — no public upload UI.

## Retrieval eval

Gold questions live in `evals/pl_handbook.jsonl`. Measure Hit@k / MRR without calling Groq:

```bash
python -m app.eval_retrieval
```

Hybrid retrieval (semantic + BM25 RRF re-rank) is controlled in `config/config.yaml` under `retrieval.hybrid`.

## Domain Layer

| Path | Role |
| ---- | ---- |
| `config/config.yaml` | Portfolio deploy (`ui.mode: portfolio`) |
| `config/config.playground.yaml` | Self-serve playground deploy |
| `prompts/system.txt` | Handbook Q&A persona |
| `prompts/not_found.txt` | Guardrail when context is insufficient |
| `frontend/` | Product chrome |

Foundation code under `app/core/` should not absorb business rules unless they pass ADR-0002 (proven reuse + config-only).

## Template upstream

Important Foundation fixes are ported manually from `knowledge-application-template` until a later `rag-core` package exists. No automatic sync.

## Tests

```bash
pytest
```
