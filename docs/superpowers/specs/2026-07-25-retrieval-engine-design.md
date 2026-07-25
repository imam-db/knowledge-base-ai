# Milestone 2: Retrieval Engine Design

**Project:** Knowledge Base AI  
**Date:** 2026-07-25  
**Scope:** Document search over ChromaDB only. No prompt building, Groq, or LLM (Milestone 3).

## Goal

Given a natural-language query, return the top-K most relevant chunks from collection `knowledge_base` as typed `SearchResult` objects, using the same embedding model as Milestone 1.

## Non-goals

- Prompt building / LLM / Groq
- Similarity threshold filtering
- Converting distance → similarity %
- FastAPI / UI

## Decisions

| Topic | Decision |
|-------|----------|
| Branch | `feature/m2-retrieval` from `main` (after M1 merge) |
| Empty collection / 0 hits | Return `[]` + `logging.warning` |
| `SearchResult` location | `app/retrieve.py` (no separate models file yet) |
| Architecture | Thin orchestration in `retrieve.py`; Chroma query only in `chroma.py` |
| Empty / whitespace query | Return `[]` + warning (skip encode) |
| Distance | Raw Chroma distance (no conversion) |
| Default `top_k` | 5 |

## Architecture

```
query → embed_texts([query]) → chroma.query_similar(...) → List[SearchResult]
```

| Module | Change |
|--------|--------|
| `app/chroma.py` | Add `query_similar(query_embedding, n_results, collection=None)` returning raw ids/documents/metadatas/distances |
| `app/retrieve.py` | `SearchResult`, `search()`, logging, CLI |
| `app/embedding.py` | Unchanged — reuse singleton model via `embed_texts` / `get_model` |

## API

```python
@dataclass
class SearchResult:
    rank: int
    document_name: str
    page: int
    chunk_id: int
    distance: float
    text: str

def search(query: str, top_k: int = 5) -> list[SearchResult]:
    ...
```

Missing metadata fallbacks: `document_name=""`, `page=1`, `chunk_id=0`.

## Logging (stdlib `logging`, INFO)

1. Loading embedding model (before encode / when model loads)
2. Encoding query
3. Querying Chroma
4. Number of chunks retrieved

## CLI

```bash
python app/retrieve.py "Bagaimana prosedur cuti?"
python app/retrieve.py "Bagaimana prosedur cuti?" --verbose
```

Default: readable ranked blocks (document, page, chunk, distance, text).  
`--verbose`: embed ms, Chroma ms, result count, collection name, embedding model name.

## Verification

Run several queries against ingested docs; confirm top-K relevance and raw distances look sensible (ordered, not random).
