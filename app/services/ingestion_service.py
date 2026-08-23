from __future__ import annotations

import io
import zipfile
from pathlib import Path

from app.config import make_document_id, settings
from app.ingest import IngestLoadError, ingest_file
from app.loaders import SUPPORTED_SUFFIXES


class UploadValidationError(Exception):
    """Client-fixable upload / ingest validation failure (map to HTTP 400)."""


def safe_document_name(filename: str | None) -> str:
    if not filename or not str(filename).strip():
        raise UploadValidationError("Invalid file name")
    name = Path(filename).name.strip()
    if not name or name in {".", ".."} or ".." in name:
        raise UploadValidationError("Invalid file name")
    if "/" in name or "\\" in name:
        raise UploadValidationError("Invalid file name")
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise UploadValidationError("Unsupported file type. Only .pdf and .docx are allowed")
    return name


def assert_within_size_limit(content: bytes) -> None:
    if len(content) > settings.max_upload_bytes:
        raise UploadValidationError("File too large (max 20MB)")
    if len(content) == 0:
        raise UploadValidationError("Unsupported document")


def _is_pdf(content: bytes) -> bool:
    return content.startswith(b"%PDF")


def _is_docx(content: bytes) -> bool:
    if not content.startswith(b"PK"):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            return any(name.startswith("word/") for name in zf.namelist())
    except zipfile.BadZipFile:
        return False


def assert_content_matches_extension(name: str, content: bytes) -> None:
    suffix = Path(name).suffix.lower()
    if suffix == ".pdf" and _is_pdf(content):
        return
    if suffix == ".docx" and _is_docx(content):
        return
    raise UploadValidationError("Unsupported document")


def ingest_uploaded_file(*, filename: str, content: bytes) -> dict[str, str | int]:
    """Validate, save under documents/, run existing ingest_file, rollback on failure."""
    name = safe_document_name(filename)
    assert_within_size_limit(content)
    assert_content_matches_extension(name, content)

    docs_dir = settings.documents_dir
    docs_dir.mkdir(parents=True, exist_ok=True)
    dest = docs_dir / name

    backup: bytes | None = dest.read_bytes() if dest.exists() else None
    dest.write_bytes(content)

    document_id = make_document_id(name)
    try:
        chunks_created, _sample = ingest_file(dest)
    except IngestLoadError as exc:
        _rollback_file(dest, backup)
        raise UploadValidationError(f"Unsupported document: {exc}") from exc
    except Exception:
        _rollback_file(dest, backup)
        raise

    if chunks_created <= 0:
        _rollback_file(dest, backup)
        raise UploadValidationError("Document produced no usable content")

    return {
        "document_id": document_id,
        "document_name": name,
        "chunks_created": chunks_created,
        "status": "ready",
    }


def _rollback_file(dest: Path, backup: bytes | None) -> None:
    if backup is None:
        dest.unlink(missing_ok=True)
    else:
        dest.write_bytes(backup)
