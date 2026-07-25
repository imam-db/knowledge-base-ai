# Milestone 2: Retrieval Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Add typed top-K retrieval over ChromaDB with a readable CLI, reusing M1 embedding + chroma helpers.

**Architecture:** `retrieve.search` orchestrates; `chroma.query_similar` owns all Chroma query calls; `embed_texts` reuses the M1 model singleton.

**Tech Stack:** Existing M1 stack (sentence-transformers, chromadb, argparse, logging).

**Spec:** `docs/superpowers/specs/2026-07-25-retrieval-engine-design.md`

---

### Task 1: `query_similar` in `chroma.py` (TDD)

**Files:**
- Modify: `app/chroma.py`
- Create: `tests/test_chroma_query.py`

- [ ] **Step 1: Write failing test** for a thin wrapper that accepts a fake collection (inject `collection=`). Mock `collection.query` to return one hit; assert `query_similar` passes `query_embeddings` and `n_results` and returns documents/metadatas/distances lists.

- [ ] **Step 2: Implement**

```python
def query_similar(
    query_embedding: Sequence[float],
    n_results: int = 5,
    collection: Collection | None = None,
) -> dict[str, Any]:
    """Query collection by embedding. Returns Chroma query result dict for one query."""
    coll = collection or get_collection()
    if coll.count() == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    return coll.query(
        query_embeddings=[list(query_embedding)],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
```

- [ ] **Step 3: pytest pass + commit** `Add Chroma query_similar helper for retrieval`

---

### Task 2: `retrieve.py` search + CLI (TDD)

**Files:**
- Create: `app/retrieve.py`
- Create: `tests/test_retrieve.py`

- [ ] **Step 1: Tests** — empty query → `[]`; mapping from mocked chroma/embed produces ranked `SearchResult` with raw distance; sequential ranks 1..N.

- [ ] **Step 2: Implement** `SearchResult`, `search()`, `_format_results()`, argparse CLI, logging, timing for `--verbose`. Lazy-import heavy deps if needed so unit tests of formatting/mapping stay light. `sys.path` bootstrap like `ingest.py`.

- [ ] **Step 3: pytest + commit** `Add retrieval search API and CLI`

---

### Task 3: Manual verification

- [ ] Ensure worktree has `.venv`, `.env`, sample docs, and `chroma_db` (copy from M1 worktree or re-ingest).
- [ ] Run `python app/retrieve.py "reset password"` and a cuti-related query; confirm relevant chunks + distances.
- [ ] Run with `--verbose`; confirm timings printed.
- [ ] Commit only code/docs changes (not chroma_db / sample binaries unless asked).
