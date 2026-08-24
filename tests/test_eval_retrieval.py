from __future__ import annotations

from app.eval_retrieval import EvalCase, CaseResult, first_hit_rank, summarize


def test_first_hit_rank_finds_earliest_page():
    assert first_hit_rank([10, 63, 63], [63, 64]) == 2
    assert first_hit_rank([1, 2], [99]) is None


def test_summarize_hit_at_k_and_mrr():
    cases = [
        CaseResult(
            case=EvalCase("a", "q1", True, [63]),
            hit=True,
            reciprocal_rank=1.0,
            filtered_empty=False,
            retrieved_pages=[63],
        ),
        CaseResult(
            case=EvalCase("b", "q2", True, [148]),
            hit=True,
            reciprocal_rank=0.5,
            filtered_empty=False,
            retrieved_pages=[1, 148],
        ),
        CaseResult(
            case=EvalCase("c", "q3", False, []),
            hit=None,
            reciprocal_rank=None,
            filtered_empty=True,
            retrieved_pages=[9],
        ),
    ]
    summary = summarize(cases)
    assert summary["hit_at_k"] == 1.0
    assert summary["mrr"] == 0.75
    assert summary["unanswerable_empty_rate"] == 1.0
