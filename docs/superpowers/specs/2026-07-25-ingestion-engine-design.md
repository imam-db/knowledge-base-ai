# Milestone 1: Ingestion Engine Design

**Project:** Knowledge Base AI (RAG for internal company documents)  
**Date:** 2026-07-25  
**Scope:** Ingestion only — load, clean, chunk, embed, persist to ChromaDB. No retrieval, LLM, API, or UI.

## Goal

Index PDF and DOCX files from `documents/` into a local ChromaDB collection so later milestones can retrieve and answer questions. Running the ingest script twice for the same file must replace prior chunks, not duplicate them.

## Non-goals (later milestones)

- Retrieval / similarity search
- Prompt building or LLM (e.g. Groq)
- REST API or UI
- LangChain chains, agents, memory, or runnables

## Stack

| Concern | Choice |
|---------|--------|
| Language | Python 3.10+ |
| PDF load | `PyPDFLoader` (`langchain-community`) |
| DOCX load | `Docx2txtLoader` (`langchain-community`) |
| Chunking | `RecursiveCharacterTextSplitter` (`langchain`), `chunk_size=700`, `chunk_overlap=100` |
| Embedding | `sentence-transformers`, model `paraphrase-multilingual-MiniLM-L12-v2` (local) |
| Vector store | `chromadb` `PersistentClient`, path `./chroma_db`, collection `knowledge_base` |

LangChain is used **only** for loaders and the text splitter.

## Project layout (workspace root = `rag/`)

```
rag/
├── app/
│   ├── main.py          # stub placeholder until Milestone 4/5
│   ├── config.py
│   ├── ingest.py        # runnable: python app/ingest.py
│   ├── embedding.py
│   ├── chroma.py
│   └── loaders.py
├── documents/
├── chroma_db/           # created at runtime
├── requirements.txt
├── .env
└── docs/superpowers/specs/
```

## Architecture

Thin modules; orchestration lives only in `ingest.py`.

```
documents/ → loaders.py (load + clean)
                ↓
            ingest.py (chunk + attach metadata)
                ↓
         embedding.py → chroma.py → ./chroma_db
```

| Module | Responsibility |
|--------|----------------|
| `config.py` | Paths, collection name, chunk params, embedding model name, cleaning regex patterns (defaults + `.env`) |
| `loaders.py` | Discover PDF/DOCX, load via LangChain loaders, apply configurable cleaning |
| `embedding.py` | Lazy-load sentence-transformers model; `embed_texts(list[str]) → list[list[float]]` |
| `chroma.py` | PersistentClient; delete-by-`document_id` then add vectors + metadata |
| `ingest.py` | End-to-end pipeline + CLI entry + summary print |
| `main.py` | Stub only — no duplicate ingest logic |

## Data flow (per file)

1. Scan `documents/` for `.pdf` / `.docx` (case-insensitive). Other extensions ignored.
2. Derive stable `document_id = uuid.uuid5(uuid.NAMESPACE_URL, document_name)` so re-ingest of the same filename replaces the same logical document.
3. Load pages/segments. For PDF, use page numbers from loader metadata. For DOCX (or any segment without page metadata), set **`page = 1` always** (never `null` or `0`) so citation logic in Milestone 3 stays simple.
4. Clean each text segment with configurable regex patterns.
5. Split with `RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)`.
6. Attach metadata to every chunk:

```python
{
  "document_id": "<uuid5-string>",
  "document_name": "nama_file.pdf",
  "page": 8,                    # int; DOCX default 1
  "chunk_id": 12,               # 0-based index within this document
  "uploaded_at": "2026-07-25"   # date.today().isoformat()
}
```

7. Embed chunk texts in batch via sentence-transformers.
8. Persist to Chroma: chunk id = `{document_id}_{chunk_id}`.

### Replace semantics

Before adding chunks for a document:

```text
collection.delete(where={"document_id": "<uuid5>"})
```

Then `add` documents, embeddings, metadatas, and ids.

## Cleaning

Configurable patterns in `config` / `.env`, with sensible defaults:

- Lines that are essentially company-name / `Confidential` / `CONFIDENTIAL` headers or footers
- Standalone page-number lines (`12`, `Page 12`, `- 12 -`)
- Collapse excessive whitespace

Cleaning runs before chunking so repeated scan artifacts do not inflate the index.

## Error handling

| Condition | Behavior |
|-----------|----------|
| `documents/` missing or empty | Clear message and non-zero exit; do not pretend success |
| Single file fails to load | Log error for that file; continue with remaining files (fail-soft) |
| Empty text after cleaning | Skip empty chunks; if whole document empty, skip document with warning |
| Unsupported extension | Ignored during scan |
| Fatal Chroma / embedding failure | Abort pipeline with clear traceback |

## CLI output

`python app/ingest.py` prints:

```text
Ingestion complete
- Documents processed: N
- Chunks created: M
- Sample chunk:
  text: "..."
  metadata: {...}
```

Sample = first successfully indexed chunk; printed text may be truncated (~200 chars) for readability. Full text remains stored in Chroma.

## Configuration (`.env` / `config.py`)

At minimum:

- `DOCUMENTS_DIR` (default `./documents`)
- `CHROMA_DIR` (default `./chroma_db`)
- `CHROMA_COLLECTION` (default `knowledge_base`)
- `CHUNK_SIZE` / `CHUNK_OVERLAP` (700 / 100)
- `EMBEDDING_MODEL` (`paraphrase-multilingual-MiniLM-L12-v2`)
- Optional cleaning pattern overrides

## Verification (manual, Milestone 1)

1. Place at least one PDF (optional: one DOCX) under `documents/`.
2. Run `python app/ingest.py` — confirm counts and sample metadata.
3. Run again — confirm no duplicate chunks for the same `document_id` (replace works).

Automated unit tests are optional for M1.

## Decisions log

| Topic | Decision |
|-------|----------|
| Re-ingest | Replace chunks for that `document_id` |
| `document_id` | Stable UUID5 from `document_name` |
| Project root | Use existing `rag/` workspace (no nested `knowledge-base-ai/`) |
| `main.py` | Stub placeholder only |
| DOCX `page` | Always `1` |
| Module style | Thin modules + pipeline in `ingest.py` |
