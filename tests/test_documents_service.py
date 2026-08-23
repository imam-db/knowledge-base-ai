from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.config import make_document_id
from app.services.documents_service import (
    DocumentDeleteError,
    DocumentNotFoundError,
    delete_document,
    get_stats,
    list_documents,
)


def test_get_stats_counts_unique_documents_and_chunks():
    coll = MagicMock()
    coll.count.return_value = 3
    metadatas = [
        {"document_name": "a.pdf", "page": 1},
        {"document_name": "a.pdf", "page": 2},
        {"document_name": "b.pdf", "page": 1},
    ]
    with (
        patch("app.services.documents_service.get_collection", return_value=coll),
        patch("app.services.documents_service.get_all_metadatas", return_value=metadatas),
    ):
        assert get_stats() == {"documents": 2, "chunks": 3}


def test_list_documents_groups_max_page_and_uploaded_at():
    metadatas = [
        {"document_name": "SOP.pdf", "page": 1, "uploaded_at": "2026-07-25"},
        {"document_name": "SOP.pdf", "page": 4, "uploaded_at": "2026-07-25"},
        {"document_name": "FAQ.docx", "page": 1, "uploaded_at": "2026-07-24"},
    ]
    with patch("app.services.documents_service.get_all_metadatas", return_value=metadatas):
        result = list_documents()
    assert result["documents"] == [
        {
            "document_id": make_document_id("FAQ.docx"),
            "name": "FAQ.docx",
            "pages": 1,
            "uploaded_at": "2026-07-24",
        },
        {
            "document_id": make_document_id("SOP.pdf"),
            "name": "SOP.pdf",
            "pages": 4,
            "uploaded_at": "2026-07-25",
        },
    ]


def test_list_documents_includes_document_id():
    metadatas = [
        {
            "document_id": "11111111-1111-5111-8111-111111111111",
            "document_name": "SOP.pdf",
            "page": 1,
            "uploaded_at": "2026-07-25",
        },
        {
            "document_id": "11111111-1111-5111-8111-111111111111",
            "document_name": "SOP.pdf",
            "page": 4,
            "uploaded_at": "2026-07-25",
        },
        {
            "document_name": "FAQ.docx",
            "page": 1,
            "uploaded_at": "2026-07-24",
        },
    ]
    with patch("app.services.documents_service.get_all_metadatas", return_value=metadatas):
        result = list_documents()
    assert result["documents"] == [
        {
            "document_id": make_document_id("FAQ.docx"),
            "name": "FAQ.docx",
            "pages": 1,
            "uploaded_at": "2026-07-24",
        },
        {
            "document_id": "11111111-1111-5111-8111-111111111111",
            "name": "SOP.pdf",
            "pages": 4,
            "uploaded_at": "2026-07-25",
        },
    ]


def test_delete_document_not_found():
    with patch(
        "app.services.documents_service.get_chunks_for_document",
        return_value=[],
    ):
        with pytest.raises(DocumentNotFoundError):
            delete_document("missing-id")


def test_delete_document_happy_path(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.documents_service.settings.documents_dir",
        tmp_path,
    )
    path = tmp_path / "a.pdf"
    path.write_bytes(b"%PDF")
    metas = [
        {"document_id": "id-1", "document_name": "a.pdf"},
        {"document_id": "id-1", "document_name": "a.pdf"},
    ]
    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, []],
        ),
        patch("app.services.documents_service.delete_document_chunks") as del_chunks,
    ):
        result = delete_document("id-1")
    del_chunks.assert_called_once_with("id-1")
    assert result == {
        "document_id": "id-1",
        "document_name": "a.pdf",
        "chunks_deleted": 2,
        "status": "deleted",
    }
    assert not path.exists()


def test_delete_document_missing_file_still_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.documents_service.settings.documents_dir",
        tmp_path,
    )
    metas = [{"document_id": "id-1", "document_name": "gone.pdf"}]
    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, []],
        ),
        patch("app.services.documents_service.delete_document_chunks"),
    ):
        result = delete_document("id-1")
    assert result["status"] == "deleted"
    assert result["chunks_deleted"] == 1


def test_delete_document_unlink_failure_does_not_rollback_chunks(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "app.services.documents_service.settings.documents_dir",
        tmp_path,
    )
    path = tmp_path / "a.pdf"
    path.write_bytes(b"%PDF")
    metas = [{"document_id": "id-1", "document_name": "a.pdf"}]
    real_unlink = Path.unlink

    def boom(self, *args, **kwargs):
        if self == path:
            raise OSError("permission denied")
        return real_unlink(self, *args, **kwargs)

    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, []],
        ),
        patch("app.services.documents_service.delete_document_chunks") as del_chunks,
        patch.object(Path, "unlink", boom),
    ):
        with pytest.raises(DocumentDeleteError, match="file"):
            delete_document("id-1")
    del_chunks.assert_called_once_with("id-1")
    # chunks already deleted — no rollback API called


def test_delete_document_verify_chunks_remain_raises():
    metas = [{"document_id": "id-1", "document_name": "a.pdf"}]
    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, metas],  # still present after delete
        ),
        patch("app.services.documents_service.delete_document_chunks"),
    ):
        with pytest.raises(DocumentDeleteError, match="chunks"):
            delete_document("id-1")


@pytest.mark.parametrize("unsafe_name", ["../a.pdf", "foo/a.pdf"])
def test_delete_document_sanitizes_document_name_basename(
    tmp_path, monkeypatch, unsafe_name
):
    monkeypatch.setattr(
        "app.services.documents_service.settings.documents_dir",
        tmp_path,
    )
    target = tmp_path / "a.pdf"
    target.write_bytes(b"%PDF")
    escaped = tmp_path.parent / "a.pdf"
    escaped.write_bytes(b"trap")

    metas = [{"document_id": "id-1", "document_name": unsafe_name}]
    with (
        patch(
            "app.services.documents_service.get_chunks_for_document",
            side_effect=[metas, []],
        ),
        patch("app.services.documents_service.delete_document_chunks"),
    ):
        result = delete_document("id-1")

    assert result["document_name"] == "a.pdf"
    assert not target.exists()
    assert escaped.exists()
