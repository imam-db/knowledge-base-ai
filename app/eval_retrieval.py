from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.answer import _filter_chunks
from app.config import settings
from app.retrieve import search

logger = logging.getLogger(__name__)

DEFAULT_EVAL_PATH = _ROOT / "evals" / "pl_handbook.jsonl"


@dataclass
class EvalCase:
    id: str
    question: str
    answerable: bool
    expected_pages: list[int]
    notes: str = ""


@dataclass
class CaseResult:
    case: EvalCase
    hit: bool | None
    reciprocal_rank: float | None
    filtered_empty: bool
    retrieved_pages: list[int]


def load_eval_cases(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            data = json.loads(raw)
            cases.append(
                EvalCase(
                    id=str(data["id"]),
                    question=str(data["question"]),
                    answerable=bool(data["answerable"]),
                    expected_pages=[int(p) for p in (data.get("expected_pages") or [])],
                    notes=str(data.get("notes") or ""),
                )
            )
            if not cases[-1].question:
                raise ValueError(f"Empty question at line {line_no}")
    return cases


def first_hit_rank(retrieved_pages: Sequence[int], expected_pages: Sequence[int]) -> int | None:
    expected = set(expected_pages)
    for rank, page in enumerate(retrieved_pages, start=1):
        if page in expected:
            return rank
    return None


def evaluate_case(case: EvalCase, *, top_k: int) -> CaseResult:
    hits = search(case.question, top_k=top_k)
    filtered = _filter_chunks(hits, settings.retrieval.distance_threshold)
    retrieved_pages = [h.page for h in hits]
    filtered_empty = len(filtered) == 0

    if case.answerable:
        rank = first_hit_rank(retrieved_pages, case.expected_pages)
        return CaseResult(
            case=case,
            hit=rank is not None,
            reciprocal_rank=(1.0 / rank) if rank else 0.0,
            filtered_empty=filtered_empty,
            retrieved_pages=retrieved_pages,
        )

    return CaseResult(
        case=case,
        hit=None,
        reciprocal_rank=None,
        filtered_empty=filtered_empty,
        retrieved_pages=retrieved_pages,
    )


def summarize(results: Sequence[CaseResult]) -> dict[str, Any]:
    answerable = [r for r in results if r.case.answerable]
    unanswerable = [r for r in results if not r.case.answerable]
    hits = sum(1 for r in answerable if r.hit)
    mrr = (
        sum(r.reciprocal_rank or 0.0 for r in answerable) / len(answerable) if answerable else 0.0
    )
    unans_pass = (
        sum(1 for r in unanswerable if r.filtered_empty) / len(unanswerable)
        if unanswerable
        else 0.0
    )
    return {
        "n_answerable": len(answerable),
        "n_unanswerable": len(unanswerable),
        "hit_at_k": hits / len(answerable) if answerable else 0.0,
        "mrr": mrr,
        "unanswerable_empty_rate": unans_pass,
        "misses": [r.case.id for r in answerable if not r.hit],
    }


def run_eval(path: Path, *, top_k: int) -> dict[str, Any]:
    cases = load_eval_cases(path)
    results = [evaluate_case(case, top_k=top_k) for case in cases]
    summary = summarize(results)
    summary["hybrid_enabled"] = settings.retrieval.hybrid.enabled
    summary["top_k"] = top_k
    summary["eval_path"] = str(path)
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate retrieval against a gold JSONL set")
    parser.add_argument(
        "--eval-path",
        type=Path,
        default=DEFAULT_EVAL_PATH,
        help="Path to eval JSONL",
    )
    parser.add_argument("--top-k", type=int, default=None, help="Override retrieval top_k")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpcore", "huggingface_hub", "sentence_transformers", "chromadb"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    top_k = args.top_k if args.top_k is not None else settings.retrieval.top_k
    summary = run_eval(args.eval_path, top_k=top_k)

    print("Retrieval eval")
    print(f"- path              : {summary['eval_path']}")
    print(f"- hybrid            : {summary['hybrid_enabled']}")
    print(f"- top_k             : {summary['top_k']}")
    print(f"- answerable        : {summary['n_answerable']}")
    print(f"- unanswerable      : {summary['n_unanswerable']}")
    print(f"- Hit@{summary['top_k']}            : {summary['hit_at_k']:.3f}")
    print(f"- MRR               : {summary['mrr']:.3f}")
    print(f"- unanswerable empty: {summary['unanswerable_empty_rate']:.3f}")
    if summary["misses"]:
        print(f"- misses            : {', '.join(summary['misses'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
