from __future__ import annotations

import re
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_core.documents import Document

from app.config import Settings, settings

SUPPORTED_SUFFIXES = {".pdf", ".docx"}


def clean_text(text: str, patterns: list[re.Pattern[str]]) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if any(p.match(line.strip()) for p in patterns):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_page(raw_page: int | None, *, has_page_metadata: bool) -> int:
    """Store 1-based pages. DOCX / missing metadata always returns 1."""
    if not has_page_metadata or raw_page is None:
        return 1
    # PyPDFLoader uses 0-based page in metadata
    return int(raw_page) + 1


def discover_documents(directory: Path | None = None) -> list[Path]:
    directory = directory or settings.documents_dir
    if not directory.exists():
        return []
    files = [
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    return sorted(files, key=lambda p: p.name.lower())


def load_file(path: Path, cfg: Settings | None = None) -> list[Document]:
    """Load one file into per-page/segment Documents with cleaned text and normalized page."""
    cfg = cfg or settings
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raw_docs = PyPDFLoader(str(path)).load()
        has_page = True
    elif suffix == ".docx":
        raw_docs = Docx2txtLoader(str(path)).load()
        has_page = False
    else:
        raise ValueError(f"Unsupported file type: {path}")

    patterns = cfg.cleaning_patterns()
    out: list[Document] = []
    for doc in raw_docs:
        page_raw = doc.metadata.get("page") if has_page else None
        page = normalize_page(page_raw if isinstance(page_raw, int) else None, has_page_metadata=has_page)
        text = clean_text(doc.page_content or "", patterns)
        if not text:
            continue
        out.append(
            Document(
                page_content=text,
                metadata={
                    "page": page,
                    "source": str(path),
                    "document_name": path.name,
                },
            )
        )
    return out
