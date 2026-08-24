# Phase B: Retrieval Quality (Eval + Hybrid)

**Status:** Approved (B1+B2)  
**Date:** 2026-08-23  
**Product:** Knowledge Base AI (Premier League handbook portfolio)

## Goal

Make grounded answers more reliable by (1) measuring retrieval with a fixed eval set, and (2) adding hybrid retrieval (semantic + keyword) with RRF fusion.

## Non-goals (later phases)

- Streaming answers, source preview, shareable `?q=` (Phase C)
- Cross-encoder reranker model (optional Full B later)
- Rate limits / production hardening (Phase E)

## Design

### 1. Eval set

- Path: `evals/pl_handbook.jsonl`
- ~25 English questions grounded in `plhandbook.pdf`
- Fields per line:
  - `id`, `question`, `answerable` (bool)
  - `expected_pages` (list of ints; empty if unanswerable)
  - `notes` (optional)
- Success metrics (retrieval only, no LLM required for CI):
  - **Hit@k**: any retrieved page intersects `expected_pages` (answerable only)
  - **MRR**: reciprocal rank of first page hit
  - **Unanswerable pass rate**: no chunk passes distance threshold (or empty after filter)

Runner: `python -m app.eval_retrieval`  
Prints baseline metrics; exit non-zero if Hit@5 drops below a configured floor after hybrid is enabled (soft floor documented in runner).

### 2. Hybrid retrieval

When `retrieval.hybrid.enabled` is true:

1. Semantic: Chroma `query_similar` with `n_results = candidate_k` (default 20)
2. Keyword: BM25 over all indexed chunk texts (lazy in-memory index from Chroma `get`)
3. Fuse with **Reciprocal Rank Fusion** (`score = Σ 1/(k + rank)`, `k=60`)
4. Return top `top_k` fused results as `SearchResult`
5. Distance field: keep Chroma L2 distance when the chunk appeared in the semantic list; otherwise set `distance` to a large sentinel so answer threshold still requires semantic support **unless** the chunk is in the top `keyword_boost_ranks` BM25 hits (then treat as passing by assigning `distance = min(threshold, best_semantic_or_0)`)

Practical v1 rule (implemented):

- RRF fuses semantic + BM25 rankings
- **Only chunks that appear in the semantic candidate pool are returned**
- Distances always come from Chroma — BM25 only re-ranks (exact handbook terms bubble up)
- `keyword_pass_rank` is reserved/unused in this mode (set `0`)

This preserves unanswerable guardrails while improving ranking for term-heavy queries.

### 3. Config (`config.yaml`)

```yaml
retrieval:
  distance_threshold: 25.0
  top_k: 5
  candidate_k: 20
  hybrid:
    enabled: true
    rrf_k: 60
    keyword_pass_rank: 3
```

### 4. Dependencies

- Add `rank-bm25` for BM25 indexing.

### 5. Files

| Path | Role |
|------|------|
| `evals/pl_handbook.jsonl` | Gold questions |
| `app/eval_retrieval.py` | Metrics runner |
| `app/keyword_index.py` | BM25 index over Chroma |
| `app/retrieve.py` | Hybrid search entry |
| `app/config.py` + `config/*.yaml` | Knobs |
| `tests/test_hybrid_retrieve.py` | Unit tests with mocks |
| `tests/test_eval_retrieval.py` | Metrics helpers |

## Acceptance

1. Eval runner runs without Groq key
2. With hybrid on, Hit@5 on answerable items ≥ baseline (semantic-only) or improves
3. Existing unit tests still pass
4. Example questions from UI still return grounded answers
