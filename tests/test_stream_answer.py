from __future__ import annotations

from unittest.mock import patch

from app.answer import _build_sources, _classify_status, _snippet, iter_answer_events
from app.retrieve import SearchResult


def _chunk(
    page: int = 63,
    text: str = "each Club shall play two League Matches",
    distance: float = 10.0,
) -> SearchResult:
    return SearchResult(
        rank=1,
        document_name="plhandbook.pdf",
        page=page,
        chunk_id=0,
        distance=distance,
        text=text,
        chroma_id="id-1",
    )


def test_snippet_truncates():
    long = "word " * 80
    out = _snippet(long, max_len=40)
    assert len(out) <= 40
    assert out.endswith("…")


def test_build_sources_includes_snippet():
    sources = _build_sources([_chunk()])
    assert sources[0]["document"] == "plhandbook.pdf"
    assert sources[0]["page"] == 63
    assert "League Matches" in sources[0]["snippet"]


def test_classify_status_not_found_without_sources():
    assert _classify_status("anything", []) == "not_found"


def test_iter_answer_events_not_found_skips_llm():
    with (
        patch("app.answer.search", return_value=[_chunk(distance=99.0)]),
        patch("app.answer.get_llm_provider") as llm_mock,
    ):
        events = list(iter_answer_events("unrelated?"))
    assert events[0]["event"] == "status"
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["status"] == "not_found"
    llm_mock.assert_not_called()


def test_iter_answer_events_streams_tokens():
    with (
        patch("app.answer.search", return_value=[_chunk()]),
        patch("app.answer.get_llm_provider") as llm_mock,
        patch("app.answer.settings") as settings_mock,
    ):
        settings_mock.retrieval.top_k = 5
        settings_mock.retrieval_distance_threshold = 25.0
        settings_mock.groq_api_key = "test-key"
        llm_mock.return_value.generate_stream.return_value = iter(["Hello", " world"])
        events = list(iter_answer_events("How many League Matches?"))

    kinds = [e["event"] for e in events]
    assert "sources" in kinds
    assert kinds.count("token") == 2
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["answer"] == "Hello world"
    assert events[-1]["data"]["status"] == "answered"
