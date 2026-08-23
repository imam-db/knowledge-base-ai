from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

with (
    patch("app.main.get_model"),
    patch("app.main.get_collection"),
):
    from app.main import app

client = TestClient(app)


def test_delete_requires_api_key(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    res = client.delete("/api/v1/documents/some-id")
    assert res.status_code == 401


def test_delete_rejects_wrong_api_key(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    res = client.delete(
        "/api/v1/documents/some-id",
        headers={"X-API-Key": "wrong"},
    )
    assert res.status_code == 401


def test_delete_not_found(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    from app.services.documents_service import DocumentNotFoundError

    with patch(
        "app.api.routes.documents_service.delete_document",
        side_effect=DocumentNotFoundError("Document not found"),
    ):
        res = client.delete(
            "/api/v1/documents/missing",
            headers={"X-API-Key": "secret-key"},
        )
    assert res.status_code == 404
    assert res.json()["detail"] == "Document not found"


def test_delete_success(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    payload = {
        "document_id": "id-1",
        "document_name": "a.pdf",
        "chunks_deleted": 3,
        "status": "deleted",
    }
    with patch(
        "app.api.routes.documents_service.delete_document",
        return_value=payload,
    ) as mocked:
        res = client.delete(
            "/api/v1/documents/id-1",
            headers={"X-API-Key": "secret-key"},
        )
    assert res.status_code == 200
    assert res.json() == payload
    mocked.assert_called_once_with("id-1")


def test_delete_maps_delete_error_to_500(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    from app.services.documents_service import DocumentDeleteError

    with patch(
        "app.api.routes.documents_service.delete_document",
        side_effect=DocumentDeleteError("Failed to delete document file"),
    ):
        res = client.delete(
            "/api/v1/documents/id-1",
            headers={"X-API-Key": "secret-key"},
        )
    assert res.status_code == 500
    assert res.json()["detail"] == "Failed to delete document file"
