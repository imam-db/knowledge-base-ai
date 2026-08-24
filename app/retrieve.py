from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.chroma import query_similar
from app.config import settings
from app.embedding import embed_texts, get_model
from app.keyword_index import get_keyword_index

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    rank: int
    document_name: str
    page: int
    chunk_id: int
    distance: float
    text: str
    chroma_id: str = ""


def _map_chroma_hits(
    documents: Sequence[str | None],
    metadatas: Sequence[dict | None],
    distances: Sequence[float | None],
    ids: Sequence[str | None] | None = None,
) -> list[SearchResult]:
    results: list[SearchResult] = []
    for idx, text in enumerate(documents):
        meta = metadatas[idx] if idx < len(metadatas) and metadatas[idx] else {}
        distance = float(distances[idx]) if idx < len(distances) and distances[idx] is not None else 0.0
        chroma_id = ""
        if ids is not None and idx < len(ids) and ids[idx] is not None:
            chroma_id = str(ids[idx])
        results.append(
            SearchResult(
                rank=idx + 1,
                document_name=str(meta.get("document_name") or ""),
                page=int(meta["page"]) if meta.get("page") is not None else 1,
                chunk_id=int(meta["chunk_id"]) if meta.get("chunk_id") is not None else 0,
                distance=distance,
                text=text or "",
                chroma_id=chroma_id,
            )
        )
    return results


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[str]],
    *,
    rrf_k: int = 60,
) -> list[tuple[str, float]]:
    """Return (id, score) sorted by descending RRF score."""
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked, start=1):
            if not item_id:
                continue
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (rrf_k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def _semantic_search(query: str, n_results: int, timings: dict[str, float] | None) -> list[SearchResult]:
    logger.info("Encoding query")
    t0 = time.perf_counter()
    vectors = embed_texts([query])
    embed_ms = (time.perf_counter() - t0) * 1000
    if timings is not None:
        timings["embed_ms"] = embed_ms
    if not vectors:
        logger.warning("Embedding produced no vector — returning no results")
        return []

    logger.info("Querying Chroma")
    t1 = time.perf_counter()
    raw = query_similar(vectors[0], n_results=n_results)
    chroma_ms = (time.perf_counter() - t1) * 1000
    if timings is not None:
        timings["chroma_ms"] = chroma_ms

    documents = (raw.get("documents") or [[]])[0] or []
    metadatas = (raw.get("metadatas") or [[]])[0] or []
    distances = (raw.get("distances") or [[]])[0] or []
    ids = (raw.get("ids") or [[]])[0] or []
    return _map_chroma_hits(documents, metadatas, distances, ids)


def _hybrid_search(
    query: str,
    *,
    top_k: int,
    candidate_k: int,
    timings: dict[str, float] | None,
) -> list[SearchResult]:
    """Fuse semantic + BM25 with RRF, but only return chunks that have Chroma distances.

    Keyword search influences ranking (exact terms bubble up) without inventing
    borderline-pass distances that hurt unanswerable guardrails.
    """
    hybrid = settings.retrieval.hybrid

    semantic = _semantic_search(query, n_results=candidate_k, timings=timings)
    t_kw = time.perf_counter()
    keyword_hits = get_keyword_index().search(query, top_k=candidate_k)
    if timings is not None:
        timings["keyword_ms"] = (time.perf_counter() - t_kw) * 1000

    if not semantic:
        return []

    semantic_by_id = {r.chroma_id: r for r in semantic if r.chroma_id}
    fused = reciprocal_rank_fusion(
        [
            [r.chroma_id for r in semantic if r.chroma_id],
            [h.chunk_id for h in keyword_hits if h.chunk_id],
        ],
        rrf_k=hybrid.rrf_k,
    )

    results: list[SearchResult] = []
    for rank, (chunk_id, _score) in enumerate(fused, start=1):
        base = semantic_by_id.get(chunk_id)
        if base is None:
            continue
        results.append(
            SearchResult(
                rank=len(results) + 1,
                document_name=base.document_name,
                page=base.page,
                chunk_id=base.chunk_id,
                distance=base.distance,
                text=base.text,
                chroma_id=base.chroma_id,
            )
        )
        if len(results) >= top_k:
            break
    return results


def search(
    query: str,
    top_k: int | None = None,
    timings: dict[str, float] | None = None,
) -> list[SearchResult]:
    """Retrieve top-K chunks for a query.

    When hybrid is enabled, fuse Chroma semantic hits with BM25 keyword hits via RRF.
    Returns raw Chroma distances when available (no answer-path threshold applied here).
    """
    cleaned = (query or "").strip()
    if not cleaned:
        logger.warning("Empty query — returning no results")
        return []

    resolved_top_k = top_k if top_k is not None else settings.retrieval.top_k
    candidate_k = max(settings.retrieval.candidate_k, resolved_top_k)

    logger.info("Loading embedding model")
    get_model()

    if settings.retrieval.hybrid.enabled:
        results = _hybrid_search(
            cleaned,
            top_k=resolved_top_k,
            candidate_k=candidate_k,
            timings=timings,
        )
    else:
        results = _semantic_search(cleaned, n_results=resolved_top_k, timings=timings)

    logger.info("Retrieved %s chunk(s)", len(results))
    if not results:
        logger.warning("No chunks retrieved for query")
    return results


def format_results(results: Sequence[SearchResult]) -> str:
    if not results:
        return "No results found.\n"

    blocks: list[str] = []
    for item in results:
        blocks.append(
            "\n".join(
                [
                    "==================================================",
                    f"Rank #{item.rank}",
                    "",
                    f"Document : {item.document_name}",
                    f"Page     : {item.page}",
                    f"Chunk    : {item.chunk_id}",
                    f"Distance : {item.distance:.4g}",
                    "",
                    "--------------------------------------------------",
                    "",
                    item.text,
                    "",
                    "==================================================",
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search the knowledge base")
    parser.add_argument("query", help="Natural-language search query")
    parser.add_argument("--top-k", type=int, default=None, dest="top_k", help="Number of chunks to return")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show embedding/Chroma timings and collection info",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpcore", "huggingface_hub", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    args = _build_parser().parse_args(list(argv) if argv is not None else None)

    timings: dict[str, float] = {}
    results = search(args.query, top_k=args.top_k, timings=timings if args.verbose else None)
    print(format_results(results), end="")

    if args.verbose:
        print("--------------------------------------------------")
        print(f"Embed time     : {timings.get('embed_ms', 0.0):.1f} ms")
        print(f"Chroma time    : {timings.get('chroma_ms', 0.0):.1f} ms")
        print(f"Keyword time   : {timings.get('keyword_ms', 0.0):.1f} ms")
        print(f"Results        : {len(results)}")
        print(f"Hybrid         : {settings.retrieval.hybrid.enabled}")
        print(f"Collection     : {settings.chroma_collection}")
        print(f"Embedding model: {settings.embedding_model}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
