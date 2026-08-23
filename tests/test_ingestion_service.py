from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.ingestion_service import (
    UploadValidationError,
    assert_content_matches_extension,
    assert_within_size_limit,
    ingest_uploaded_file,
    safe_document_name,
)


def test_safe_document_name_accepts_basename():
    assert safe_document_name("folder/SOP Cuti.pdf") == "SOP Cuti.pdf"


def test_safe_document_name_rejects_bad_types():
    with pytest.raises(UploadValidationError, match="Unsupported file type"):
        safe_document_name("notes.txt")


def test_assert_size_limit(monkeypatch):
    monkeypatch.setattr("app.services.ingestion_service.settings.max_upload_bytes", 10)
    with pytest.raises(UploadValidationError, match="too large"):
        assert_within_size_limit(b"x" * 11)


def test_pdf_magic_bytes():
    assert_content_matches_extension("a.pdf", b"%PDF-1.4 fake")
    with pytest.raises(UploadValidationError, match="Unsupported document"):
        assert_content_matches_extension("a.pdf", b"not-a-pdf")


def test_docx_requires_word_entry(tmp_path: Path):
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", "<w:document />")
    assert_content_matches_extension("a.docx", buf.getvalue())

    bad = io.BytesIO()
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("readme.txt", "hi")
    with pytest.raises(UploadValidationError, match="Unsupported document"):
        assert_content_matches_extension("a.docx", bad.getvalue())


def test_ingest_uploaded_file_success(tmp_path: Path, monkeypatch):
    docs = tmp_path / "documents"
    docs.mkdir()
    monkeypatch.setattr("app.services.ingestion_service.settings.documents_dir", docs)
    monkeypatch.setattr("app.services.ingestion_service.settings.max_upload_bytes", 1024)

    content = b"%PDF-1.4 content"
    with patch(
        "app.services.ingestion_service.ingest_file",
        return_value=(3, {"text": "x"}),
    ) as mocked:
        result = ingest_uploaded_file(filename="policy.pdf", content=content)

    assert result["chunks_created"] == 3
    assert result["document_name"] == "policy.pdf"
    assert result["status"] == "ready"
    assert (docs / "policy.pdf").read_bytes() == content
    mocked.assert_called_once()


def test_ingest_uploaded_file_empty_rolls_back_new_file(tmp_path: Path, monkeypatch):
    docs = tmp_path / "documents"
    docs.mkdir()
    monkeypatch.setattr("app.services.ingestion_service.settings.documents_dir", docs)

    with patch("app.services.ingestion_service.ingest_file", return_value=(0, None)):
        with pytest.raises(UploadValidationError, match="no usable content"):
            ingest_uploaded_file(filename="empty.pdf", content=b"%PDF-1.4")

    assert not (docs / "empty.pdf").exists()


def test_ingest_uploaded_file_empty_restores_previous(tmp_path: Path, monkeypatch):
    docs = tmp_path / "documents"
    docs.mkdir()
    dest = docs / "policy.pdf"
    dest.write_bytes(b"%PDF-1.4 old")
    monkeypatch.setattr("app.services.ingestion_service.settings.documents_dir", docs)

    with patch("app.services.ingestion_service.ingest_file", return_value=(0, None)):
        with pytest.raises(UploadValidationError, match="no usable content"):
            ingest_uploaded_file(filename="policy.pdf", content=b"%PDF-1.4 new")

    assert dest.read_bytes() == b"%PDF-1.4 old"
