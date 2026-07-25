from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    document: str
    page: int


class RetrievalMetadata(BaseModel):
    top_k: int
    returned_chunks: int
    best_distance: float | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieval_metadata: RetrievalMetadata
    confidence: float | None = None


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
