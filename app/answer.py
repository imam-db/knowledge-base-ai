from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any, Sequence

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.config import settings
from app.llm import GroqConfigError, call_groq
from app.prompts import GUARDRAIL_MESSAGE, build_prompt
from app.retrieve import SearchResult, search

logger = logging.getLogger(__name__)


def _filter_chunks(chunks: Sequence[SearchResult], threshold: float) -> list[SearchResult]:
    return [c for c in chunks if c.distance <= threshold]


def _build_sources(chunks: Sequence[SearchResult]) -> list[dict[str, Any]]:
    """Dedup by (document, page), preserving best-rank order."""
    seen: set[tuple[str, int]] = set()
    sources: list[dict[str, Any]] = []
    for chunk in chunks:
        key = (chunk.document_name, chunk.page)
        if key in seen:
            continue
        seen.add(key)
        sources.append({"document": chunk.document_name, "page": chunk.page})
    return sources


def answer_question(
    question: str,
    top_k: int = 5,
    timings: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Orchestrate retrieval → threshold filter → Groq → backend citations."""
    local_timings: dict[str, float] = {}

    t0 = time.perf_counter()
    hits = search(question, top_k=top_k)
    local_timings["retrieval_ms"] = (time.perf_counter() - t0) * 1000
    logger.info(
        "Retrieval finished in %.1f ms (%s hit(s))",
        local_timings["retrieval_ms"],
        len(hits),
    )

    filtered = _filter_chunks(hits, settings.retrieval_distance_threshold)
    logger.info(
        "Chunks passing threshold (%.2f): %s",
        settings.retrieval_distance_threshold,
        len(filtered),
    )

    best_distance = min((c.distance for c in filtered), default=None)
    metadata = {
        "top_k": top_k,
        "returned_chunks": len(filtered),
        "best_distance": best_distance,
    }

    if not filtered:
        logger.info("No chunks passed threshold — skipping Groq")
        local_timings["groq_ms"] = 0.0
        local_timings["total_ms"] = local_timings["retrieval_ms"]
        if timings is not None:
            timings.update(local_timings)
        return {
            "answer": GUARDRAIL_MESSAGE,
            "sources": [],
            "retrieval_metadata": metadata,
            "confidence": None,
        }

    prompt = build_prompt(question, filtered)

    t1 = time.perf_counter()
    answer = call_groq(prompt)
    local_timings["groq_ms"] = (time.perf_counter() - t1) * 1000
    local_timings["total_ms"] = local_timings["retrieval_ms"] + local_timings["groq_ms"]
    logger.info(
        "Groq finished in %.1f ms (total %.1f ms)",
        local_timings["groq_ms"],
        local_timings["total_ms"],
    )
    if timings is not None:
        timings.update(local_timings)

    return {
        "answer": answer,
        "sources": _build_sources(filtered),
        "retrieval_metadata": metadata,
        "confidence": None,
    }


def _format_output(
    result: dict[str, Any],
    *,
    verbose: bool,
    timings: dict[str, float] | None = None,
) -> str:
    lines = [result["answer"], "", "Sources:"]
    sources = result.get("sources") or []
    if not sources:
        lines.append("  (none)")
    else:
        for src in sources:
            lines.append(f"  - {src['document']} (page {src['page']})")

    if verbose:
        meta = result.get("retrieval_metadata") or {}
        t = timings or {}
        lines.extend(
            [
                "",
                "--------------------------------------------------",
                f"top_k           : {meta.get('top_k')}",
                f"returned_chunks : {meta.get('returned_chunks')}",
                f"best_distance   : {meta.get('best_distance')}",
                f"threshold       : {settings.retrieval_distance_threshold}",
                f"retrieval_ms    : {t.get('retrieval_ms', 0.0):.1f}",
                f"groq_ms         : {t.get('groq_ms', 0.0):.1f}",
                f"total_ms        : {t.get('total_ms', 0.0):.1f}",
                f"model           : {settings.groq_model}",
            ]
        )
    return "\n".join(lines) + "\n"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Answer a question from the knowledge base")
    parser.add_argument("question", help="Natural-language question")
    parser.add_argument("--top-k", type=int, default=5, dest="top_k")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpcore", "huggingface_hub", "sentence_transformers", "groq"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    timings: dict[str, float] = {}
    try:
        result = answer_question(
            args.question,
            top_k=args.top_k,
            timings=timings if args.verbose else None,
        )
    except GroqConfigError as exc:
        logger.error("%s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(_format_output(result, verbose=args.verbose, timings=timings), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
