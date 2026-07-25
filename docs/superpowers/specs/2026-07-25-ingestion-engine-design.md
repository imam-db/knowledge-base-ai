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

1. Scan **`documents/` flat only** (non-recursive; no subfolders). Match `.pdf` / `.docx` case-insensitively. Other extensions ignored.
2. `document_name` = basename only (e.g. `sop.pdf`). Derive stable `document_id = uuid.uuid5(uuid.NAMESPACE_URL, document_name)`. Flat scan + basename ID avoids path collisions; do not place two files with the same name (impossible in one flat folder anyway).
3. Load into **one LangChain `Document` per page/segment**, keeping page metadata on each segment:
   - PDF: use `page` from loader metadata (0- or 1-based as returned by PyPDFLoader — normalize to **1-based** for storage: `page = int(loader_page) + 1` if loader is 0-based).
   - DOCX / missing page metadata: **`page = 1` always** (never `null` or `0`).
4. Clean each segment’s text with configurable regex patterns (metadata unchanged).
5. **Split per segment, do not concatenate the whole file first.** Use `RecursiveCharacterTextSplitter(...).split_documents(page_docs)` so each chunk **inherits** its source segment’s `page`. This keeps citation metadata accurate for Milestone 3.
6. After splitting, drop empty chunks (after strip). Assign pipeline metadata on every **kept** chunk. `chunk_id` is **0-based sequential over kept chunks only** (no gaps if empties were skipped): `0, 1, 2, ...`

```python
{
  "document_id": "<uuid5-string>",
  "document_name": "nama_file.pdf",
  "page": 8,                    # int; inherited from source page; DOCX default 1
  "chunk_id": 12,               # 0-based among kept chunks only
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

**M1 does not prune orphans:** removing a file from `documents/` does **not** delete its vectors from Chroma. Only re-ingest (replace) or a future admin/delete flow clears them.

## Cleaning

Configurable patterns in `config` / `.env`. Exact default regex strings are an **implementation detail** for the plan; behaviorally they must cover:

- Lines that are essentially company-name / `Confidential` / `CONFIDENTIAL` headers or footers
- Standalone page-number lines (`12`, `Page 12`, `- 12 -`)
- Collapse excessive whitespace

Cleaning runs before chunking so repeated scan artifacts do not inflate the index. Patterns remain overridable via config.

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

- **Documents processed** = count of files successfully indexed (fail-soft skips do **not** increment N).
- **Chunks created** = total chunks written in this run.
- Sample = first successfully indexed chunk; printed text may be truncated (~200 chars) for readability. Full text remains stored in Chroma.

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
| PDF `page` through chunking | Split per page Document (inherit `page`); never concat-then-split whole file |
| PDF page numbering | Store 1-based page numbers |
| Directory scan | Flat only under `documents/` |
| Orphan files removed from disk | Not pruned from Chroma in M1 |
| Empty chunks skipped | `chunk_id` sequential on kept chunks only (no gaps) |
| Module style | Thin modules + pipeline in `ingest.py` |
