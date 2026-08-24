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
class HybridSettings:
    enabled: bool
    rrf_k: int
    keyword_pass_rank: int


@dataclass
class RetrievalSettings:
    distance_threshold: float
    top_k: int
    candidate_k: int
    hybrid: HybridSettings


@dataclass
class PipelineStepSettings:
    label: str
    detail: str


@dataclass
class EvalSettings:
    dataset: str
    questions: int
    hit_at_5: float
    mrr: float | None
    unanswerable_empty_rate: float | None
    note: str


@dataclass
class AboutSettings:
    title: str
    tagline: str
    problem: str
    approach: str
    pipeline: list[PipelineStepSettings]
    guardrails: list[str]
    tradeoffs: list[str]
    eval: EvalSettings | None


@dataclass
class UiSettings:
    mode: str
    show_documents: bool
    show_about: bool
    back_link: str
    back_label: str
    subtitle: str
    empty_state_title: str
    empty_state_description: str
    example_questions: list[str]


@dataclass
class Settings:
    app_name: str
    ui: UiSettings
    about: AboutSettings | None
    documents_dir: Path
    chroma_dir: Path
    chroma_collection: str
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    company_header: str
    retrieval: RetrievalSettings
    groq_api_key: str
    groq_model: str
    debug: bool
    admin_api_key: str
    max_upload_bytes: int

    @property
    def retrieval_distance_threshold(self) -> float:
        """Back-compat alias used across answer/retrieve modules."""
        return self.retrieval.distance_threshold

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

    ui = data.get("ui") or {}
    empty_state = ui.get("empty_state") or {}
    mode = str(ui.get("mode", "playground")).strip().lower()
    if mode not in {"portfolio", "playground"}:
        mode = "playground"
    show_documents = _as_bool(ui.get("show_documents"), default=(mode == "playground"))
    show_about = _as_bool(ui.get("show_about"), default=(mode == "portfolio"))
    example_questions_raw = ui.get("example_questions") or []
    example_questions = [
        str(item).strip() for item in example_questions_raw if str(item).strip()
    ]

    ui_settings = UiSettings(
        mode=mode,
        show_documents=show_documents,
        show_about=show_about,
        back_link=str(ui.get("back_link", "https://vvizh.com")).strip(),
        back_label=str(ui.get("back_label", "vvizh")).strip(),
        subtitle=str(
            ui.get("subtitle", "Answers grounded in indexed documents.")
        ).strip(),
        empty_state_title=str(
            empty_state.get("title", "Ask the handbook")
        ).strip(),
        empty_state_description=str(
            empty_state.get(
                "description",
                "Answers are compiled only from indexed documents.",
            )
        ).strip(),
        example_questions=example_questions,
    )

    hybrid_raw = retrieval.get("hybrid") or {}
    retrieval_settings = RetrievalSettings(
        distance_threshold=float(retrieval.get("distance_threshold", 25.0)),
        top_k=int(retrieval.get("top_k", 5)),
        candidate_k=int(retrieval.get("candidate_k", 20)),
        hybrid=HybridSettings(
            enabled=_as_bool(hybrid_raw.get("enabled"), default=False),
            rrf_k=int(hybrid_raw.get("rrf_k", 60)),
            keyword_pass_rank=int(hybrid_raw.get("keyword_pass_rank", 3)),
        ),
    )

    about_raw = data.get("about")
    about_settings: AboutSettings | None = None
    if isinstance(about_raw, dict):
        pipeline_raw = about_raw.get("pipeline") or []
        pipeline = [
            PipelineStepSettings(
                label=str(step.get("label", "")).strip(),
                detail=str(step.get("detail", "")).strip(),
            )
            for step in pipeline_raw
            if isinstance(step, dict) and str(step.get("label", "")).strip()
        ]
        guardrails_raw = about_raw.get("guardrails") or []
        tradeoffs_raw = about_raw.get("tradeoffs") or []
        eval_raw = about_raw.get("eval")
        eval_settings: EvalSettings | None = None
        if isinstance(eval_raw, dict):
            eval_settings = EvalSettings(
                dataset=str(eval_raw.get("dataset", "")).strip(),
                questions=int(eval_raw.get("questions", 0)),
                hit_at_5=float(eval_raw.get("hit_at_5", 0.0)),
                mrr=(
                    float(eval_raw["mrr"])
                    if eval_raw.get("mrr") is not None
                    else None
                ),
                unanswerable_empty_rate=(
                    float(eval_raw["unanswerable_empty_rate"])
                    if eval_raw.get("unanswerable_empty_rate") is not None
                    else None
                ),
                note=str(eval_raw.get("note", "")).strip(),
            )
        about_settings = AboutSettings(
            title=str(about_raw.get("title", "")).strip()
            or str(app.get("name", "Knowledge Application")),
            tagline=str(about_raw.get("tagline", "")).strip(),
            problem=str(about_raw.get("problem", "")).strip(),
            approach=str(about_raw.get("approach", "")).strip(),
            pipeline=pipeline,
            guardrails=[
                str(item).strip() for item in guardrails_raw if str(item).strip()
            ],
            tradeoffs=[
                str(item).strip() for item in tradeoffs_raw if str(item).strip()
            ],
            eval=eval_settings,
        )

    return Settings(
        app_name=str(app.get("name", "Knowledge Application")),
        ui=ui_settings,
        about=about_settings,
        documents_dir=_resolve_path(str(documents.get("path", "./documents"))),
        chroma_dir=_resolve_path(str(vector_store.get("path", "./chroma_db"))),
        chroma_collection=str(vector_store.get("collection", "knowledge_base")),
        chunk_size=int(chunking.get("size", 700)),
        chunk_overlap=int(chunking.get("overlap", 100)),
        embedding_model=str(
            embedding.get("model", "paraphrase-multilingual-MiniLM-L12-v2")
        ),
        company_header=str(cleaning.get("company_header", "")).strip(),
        retrieval=retrieval_settings,
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        groq_model=str(llm.get("model", "openai/gpt-oss-120b")),
        debug=_as_bool(app.get("debug"), default=False),
        admin_api_key=os.getenv("ADMIN_API_KEY", "").strip(),
        max_upload_bytes=int(max_file_size_mb) * 1024 * 1024,
    )


settings = load_settings()


def make_document_id(document_name: str) -> str:
    """Stable UUID5 from basename for replace-by-document_id."""
    name = Path(document_name).name
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))
