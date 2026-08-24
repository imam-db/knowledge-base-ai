from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.retrieve import SearchResult, search


def _disable_hybrid():
    retrieval = MagicMock()
    retrieval.hybrid.enabled = False
    retrieval.top_k = 5
    retrieval.candidate_k = 20
    return retrieval


def test_search_empty_query_returns_empty_list():
    with patch("app.retrieve.embed_texts") as embed_mock:
        assert search("   ") == []
        embed_mock.assert_not_called()


def test_search_maps_chroma_hits_to_ranked_results():
    fake_embedding = [[0.1, 0.2]]
    fake_chroma = {
        "ids": [["id-a", "id-b"]],
        "documents": [["first chunk", "second chunk"]],
        "metadatas": [
            [
                {"document_name": "SOP_HR.pdf", "page": 4, "chunk_id": 12},
                {"document_name": "FAQ.pdf", "page": 1, "chunk_id": 0},
            ]
        ],
        "distances": [[0.21, 0.44]],
    }

    with (
        patch("app.retrieve.settings") as settings_mock,
        patch("app.retrieve.get_model"),
        patch("app.retrieve.embed_texts", return_value=fake_embedding) as embed_mock,
        patch("app.retrieve.query_similar", return_value=fake_chroma) as query_mock,
    ):
        settings_mock.retrieval = _disable_hybrid()
        results = search("prosedur cuti", top_k=2)

    embed_mock.assert_called_once_with(["prosedur cuti"])
    query_mock.assert_called_once()
    assert [r.rank for r in results] == [1, 2]
    assert results[0] == SearchResult(
        rank=1,
        document_name="SOP_HR.pdf",
        page=4,
        chunk_id=12,
        distance=0.21,
        text="first chunk",
        chroma_id="id-a",
    )
    assert results[1].document_name == "FAQ.pdf"
    assert results[1].distance == 0.44


def test_search_zero_hits_returns_empty_list():
    with (
        patch("app.retrieve.settings") as settings_mock,
        patch("app.retrieve.get_model"),
        patch("app.retrieve.embed_texts", return_value=[[0.1]]),
        patch(
            "app.retrieve.query_similar",
            return_value={"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]},
        ),
    ):
        settings_mock.retrieval = _disable_hybrid()
        assert search("anything") == []
