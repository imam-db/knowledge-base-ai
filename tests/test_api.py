from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.retrieve import SearchResult

with (
    patch("app.main.get_model"),
    patch("app.main.get_collection"),
):
    from app.main import app


client = TestClient(app)


def _hit() -> SearchResult:
    return SearchResult(
        rank=1,
        document_name="a.pdf",
        page=1,
        chunk_id=0,
        distance=1.0,
        text="hello",
    )


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"service": "Knowledge Base AI", "version": "0.1.0"}


def test_ask_validation_empty_question():
    res = client.post("/api/v1/ask", json={"question": ""})
    assert res.status_code == 422


def test_ask_maps_environment_error_to_500():
    with patch(
        "app.api.routes.answer_service.ask",
        side_effect=EnvironmentError("GROQ_API_KEY tidak ditemukan di environment"),
    ):
        res = client.post("/api/v1/ask", json={"question": "Apa itu cuti?"})
    assert res.status_code == 500
    assert "GROQ_API_KEY" in res.json()["detail"]


def test_ask_success_200():
    payload = {
        "answer": "Hubungi IT Support.",
        "sources": [{"document": "sample_faq.docx", "page": 1}],
        "retrieval_metadata": {"top_k": 5, "returned_chunks": 1, "best_distance": 14.5},
        "confidence": None,
    }
    with patch("app.api.routes.answer_service.ask", return_value=payload):
        res = client.post("/api/v1/ask", json={"question": "reset password?"})
    assert res.status_code == 200
    body = res.json()
    assert body["answer"] == "Hubungi IT Support."
    assert body["sources"][0]["document"] == "sample_faq.docx"


def test_search_omits_debug_when_disabled():
    with (
        patch("app.services.retrieval_service.settings") as settings_mock,
        patch("app.services.retrieval_service.search", return_value=[_hit()]),
    ):
        settings_mock.debug = False
        res = client.post("/api/v1/search", json={"query": "hello", "top_k": 3})
    assert res.status_code == 200
    body = res.json()
    assert len(body["results"]) == 1
    assert "debug" not in body


def test_search_includes_debug_when_enabled():
    def fake_search(query, top_k=5, timings=None):
        if timings is not None:
            timings["embed_ms"] = 10.0
            timings["chroma_ms"] = 20.0
        return [_hit()]

    with (
        patch("app.services.retrieval_service.settings") as settings_mock,
        patch("app.services.retrieval_service.search", side_effect=fake_search),
    ):
        settings_mock.debug = True
        settings_mock.retrieval_distance_threshold = 25.0
        settings_mock.chroma_collection = "knowledge_base"
        res = client.post("/api/v1/search", json={"query": "hello"})
    assert res.status_code == 200
    body = res.json()
    assert body["debug"]["embedding_time_ms"] == 10.0
    assert body["debug"]["retrieval_time_ms"] == 20.0
    assert body["debug"]["collection_name"] == "knowledge_base"


def test_health():
    with patch(
        "app.api.routes.health_service.check_health",
        return_value={
            "status": "healthy",
            "embedding": "loaded",
            "vector_db": "connected",
            "groq": "configured",
        },
    ):
        res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_stats():
    with patch(
        "app.api.routes.documents_service.get_stats",
        return_value={"documents": 2, "chunks": 10},
    ):
        res = client.get("/api/v1/stats")
    assert res.status_code == 200
    assert res.json() == {"documents": 2, "chunks": 10}


def test_documents_list():
    payload = {
        "documents": [
            {"name": "sample_faq.docx", "pages": 1, "uploaded_at": "2026-07-25"},
        ]
    }
    with patch("app.api.routes.documents_service.list_documents", return_value=payload):
        res = client.get("/api/v1/documents")
    assert res.status_code == 200
    assert res.json()["documents"][0]["name"] == "sample_faq.docx"
    assert res.json()["documents"][0]["pages"] == 1
