from __future__ import annotations

from unittest.mock import patch

import pytest

from app.answer import answer_question
from app.prompts import GUARDRAIL_MESSAGE, build_prompt
from app.retrieve import SearchResult


def _chunk(**kwargs) -> SearchResult:
    defaults = {
        "rank": 1,
        "document_name": "SOP_HR.pdf",
        "page": 4,
        "chunk_id": 12,
        "distance": 10.0,
        "text": "Karyawan mengajukan cuti via HRIS.",
    }
    defaults.update(kwargs)
    return SearchResult(**defaults)


def test_build_prompt_labels_chunks():
    prompt = build_prompt("Bagaimana cuti?", [_chunk()])
    assert "[Chunk 1]" in prompt
    assert "Document: SOP_HR.pdf" in prompt
    assert "Page: 4" in prompt
    assert "Karyawan mengajukan cuti via HRIS." in prompt
    assert "Bagaimana cuti?" in prompt


def test_answer_skips_groq_when_no_chunks_pass_threshold():
    far = [_chunk(distance=99.0)]
    with (
        patch("app.answer.search", return_value=far),
        patch("app.answer.call_groq") as groq_mock,
        patch("app.answer.settings") as settings_mock,
    ):
        settings_mock.retrieval_distance_threshold = 25.0
        settings_mock.groq_api_key = "should-not-matter"
        result = answer_question("topik asing")

    groq_mock.assert_not_called()
    assert result["answer"] == GUARDRAIL_MESSAGE
    assert result["sources"] == []
    assert result["retrieval_metadata"]["returned_chunks"] == 0
    assert result["retrieval_metadata"]["best_distance"] is None
    assert result["confidence"] is None


def test_answer_raises_environment_error_when_api_key_missing():
    hits = [_chunk(distance=10.0)]
    with (
        patch("app.answer.search", return_value=hits),
        patch("app.answer.call_groq") as groq_mock,
        patch("app.answer.settings") as settings_mock,
    ):
        settings_mock.retrieval_distance_threshold = 25.0
        settings_mock.groq_api_key = ""
        with pytest.raises(EnvironmentError, match="GROQ_API_KEY tidak ditemukan"):
            answer_question("Bagaimana cuti?")

    groq_mock.assert_not_called()


def test_answer_calls_groq_and_builds_deduped_sources():
    hits = [
        _chunk(rank=1, document_name="SOP_HR.pdf", page=4, distance=10.0),
        _chunk(rank=2, document_name="SOP_HR.pdf", page=4, chunk_id=13, distance=12.0, text="detail lain"),
        _chunk(rank=3, document_name="Finance.pdf", page=8, distance=15.0, text="anggaran"),
    ]
    with (
        patch("app.answer.search", return_value=hits),
        patch("app.answer.call_groq", return_value="Ajukan cuti via HRIS.") as groq_mock,
        patch("app.answer.settings") as settings_mock,
    ):
        settings_mock.retrieval_distance_threshold = 25.0
        settings_mock.groq_api_key = "test-key"
        result = answer_question("Bagaimana cuti?", top_k=5)

    groq_mock.assert_called_once()
    assert result["answer"] == "Ajukan cuti via HRIS."
    assert result["sources"] == [
        {"document": "SOP_HR.pdf", "page": 4},
        {"document": "Finance.pdf", "page": 8},
    ]
    assert result["retrieval_metadata"]["returned_chunks"] == 3
    assert result["retrieval_metadata"]["best_distance"] == 10.0
    assert result["confidence"] is None
