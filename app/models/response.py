from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Source(BaseModel):
    document: str
    page: int
    snippet: str | None = None
    chunk_id: int | None = None
    distance: float | None = None


class RetrievalMetadata(BaseModel):
    top_k: int
    returned_chunks: int
    best_distance: float | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieval_metadata: RetrievalMetadata
    confidence: float | None = None
    status: Literal["answered", "not_found"] = "answered"


class SearchResultItem(BaseModel):
    document: str
    page: int
    chunk_id: int
    distance: float
    text: str


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    debug: dict | None = Field(default=None)


class HealthResponse(BaseModel):
    status: str
    embedding: str
    vector_db: str
    groq: str


class RootResponse(BaseModel):
    service: str
    version: str


class UiConfigResponse(BaseModel):
    app_name: str
    mode: Literal["portfolio", "playground"]
    show_documents: bool
    show_about: bool
    back_link: str
    back_label: str
    subtitle: str
    empty_state_title: str
    empty_state_description: str
    example_questions: list[str]


class PipelineStep(BaseModel):
    label: str
    detail: str


class EvalSnapshot(BaseModel):
    dataset: str
    questions: int
    hit_at_5: float
    mrr: float | None = None
    unanswerable_empty_rate: float | None = None
    note: str | None = None


class AboutLiveStats(BaseModel):
    documents: int
    chunks: int
    chunk_size: int
    chunk_overlap: int
    embedding_model: str
    llm_model: str
    hybrid_enabled: bool
    top_k: int


class AboutResponse(BaseModel):
    show: bool
    title: str | None = None
    tagline: str | None = None
    problem: str | None = None
    approach: str | None = None
    pipeline: list[PipelineStep] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    eval: EvalSnapshot | None = None
    stats: AboutLiveStats | None = None


class StatsResponse(BaseModel):
    documents: int
    chunks: int


class DocumentInfo(BaseModel):
    document_id: str
    name: str
    pages: int
    uploaded_at: str


class DeleteResponse(BaseModel):
    document_id: str
    document_name: str
    chunks_deleted: int
    status: str


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo]


class UploadResponse(BaseModel):
    document_id: str
    document_name: str
    chunks_created: int
    status: str
