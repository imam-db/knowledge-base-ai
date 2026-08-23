from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"


def _resolve_path(raw: str) -> Path:
    p = Path(raw)
    return p if p.is_absolute() else (ROOT_DIR / p).resolve()


def _config_path_from_env() -> Path:
    raw = os.getenv("CONFIG_PATH", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (ROOT_DIR / p).resolve()
    return DEFAULT_CONFIG_PATH


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    app_name: str
    documents_dir: Path
    chroma_dir: Path
    chroma_collection: str
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    company_header: str
    retrieval_distance_threshold: float
    groq_api_key: str
    groq_model: str
    debug: bool
    admin_api_key: str
    max_upload_bytes: int

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


def load_settings(config_path: Path | None = None) -> Settings:
    """Compose settings from config.yaml (application parameters) and .env (secrets)."""
    load_dotenv()

    path = config_path or _config_path_from_env()
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    app = data.get("app") or {}
    llm = data.get("llm") or {}
    embedding = data.get("embedding") or {}
    chunking = data.get("chunking") or {}
    retrieval = data.get("retrieval") or {}
    vector_store = data.get("vector_store") or {}
    documents = data.get("documents") or {}
    cleaning = data.get("cleaning") or {}

    max_file_size_mb = documents.get("max_file_size_mb", 20)

    return Settings(
        app_name=str(app.get("name", "Knowledge Application")),
        documents_dir=_resolve_path(str(documents.get("path", "./documents"))),
        chroma_dir=_resolve_path(str(vector_store.get("path", "./chroma_db"))),
        chroma_collection=str(vector_store.get("collection", "knowledge_base")),
        chunk_size=int(chunking.get("size", 700)),
        chunk_overlap=int(chunking.get("overlap", 100)),
        embedding_model=str(
            embedding.get("model", "paraphrase-multilingual-MiniLM-L12-v2")
        ),
        company_header=str(cleaning.get("company_header", "")).strip(),
        retrieval_distance_threshold=float(retrieval.get("distance_threshold", 25.0)),
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=str(llm.get("model", "llama-3.3-70b-versatile")),
        debug=_as_bool(app.get("debug"), default=False),
        admin_api_key=os.getenv("ADMIN_API_KEY", "").strip(),
        max_upload_bytes=int(max_file_size_mb) * 1024 * 1024,
    )


settings = load_settings()


def make_document_id(document_name: str) -> str:
    """Stable UUID5 from basename for replace-by-document_id."""
    name = Path(document_name).name
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))
