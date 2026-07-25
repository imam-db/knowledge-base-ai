from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root = parent of app/
ROOT_DIR = Path(__file__).resolve().parents[1]


def _path_from_env(key: str, default: str) -> Path:
    raw = os.getenv(key, default)
    p = Path(raw)
    return p if p.is_absolute() else (ROOT_DIR / p).resolve()


@dataclass
class Settings:
    documents_dir: Path = field(default_factory=lambda: _path_from_env("DOCUMENTS_DIR", "./documents"))
    chroma_dir: Path = field(default_factory=lambda: _path_from_env("CHROMA_DIR", "./chroma_db"))
    chroma_collection: str = field(default_factory=lambda: os.getenv("CHROMA_COLLECTION", "knowledge_base"))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "700")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "100")))
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
        )
    )
    # Optional company header token; empty = still match Confidential / page numbers
    company_header: str = field(default_factory=lambda: os.getenv("COMPANY_HEADER", "").strip())
    retrieval_distance_threshold: float = field(
        default_factory=lambda: float(os.getenv("RETRIEVAL_DISTANCE_THRESHOLD", "25.0"))
    )
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", "").strip())
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    )
    debug: bool = field(
        default_factory=lambda: os.getenv("DEBUG", "False").strip().lower()
        in {"1", "true", "yes", "on"}
    )

    def cleaning_patterns(self) -> list[re.Pattern[str]]:
        patterns: list[str] = [
            r"(?i)^\s*confidential\s*$",
            r"(?i)^\s*page\s+\d+\s*$",
            r"^\s*-?\s*\d+\s*-?\s*$",
        ]
        if self.company_header:
            escaped = re.escape(self.company_header)
            patterns.insert(0, rf"(?i)^\s*{escaped}\s*$")
        return [re.compile(p) for p in patterns]


settings = Settings()


def make_document_id(document_name: str) -> str:
    """Stable UUID5 from basename for replace-by-document_id."""
    name = Path(document_name).name
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))
