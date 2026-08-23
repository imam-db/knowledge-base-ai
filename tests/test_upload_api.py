from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

with (
    patch("app.main.get_model"),
    patch("app.main.get_collection"),
):
    from app.main import app


client = TestClient(app)


def test_upload_requires_api_key(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert res.status_code == 401


def test_upload_rejects_wrong_api_key(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")},
        headers={"X-API-Key": "wrong"},
    )
    assert res.status_code == 401
    assert "API key" in res.json()["detail"]


def test_upload_success(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    payload = {
        "document_id": "11111111-1111-5111-8111-111111111111",
        "document_name": "a.pdf",
        "chunks_created": 2,
        "status": "ready",
    }
    with patch(
        "app.api.routes.ingestion_service.ingest_uploaded_file",
        return_value=payload,
    ) as mocked:
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": ("a.pdf", b"%PDF-1.4 hello", "application/pdf")},
            headers={"X-API-Key": "secret-key"},
        )
    assert res.status_code == 200
    assert res.json() == payload
    mocked.assert_called_once()
    kwargs = mocked.call_args.kwargs
    assert kwargs["filename"] == "a.pdf"
    assert kwargs["content"].startswith(b"%PDF")


def test_upload_validation_error_maps_to_400(monkeypatch):
    monkeypatch.setattr("app.api.deps.settings.admin_api_key", "secret-key")
    from app.services.ingestion_service import UploadValidationError

    with patch(
        "app.api.routes.ingestion_service.ingest_uploaded_file",
        side_effect=UploadValidationError("File too large (max 20MB)"),
    ):
        res = client.post(
            "/api/v1/documents/upload",
            files={"file": ("a.pdf", b"%PDF-1.4", "application/pdf")},
            headers={"X-API-Key": "secret-key"},
        )
    assert res.status_code == 400
    assert res.json()["detail"] == "File too large (max 20MB)"
