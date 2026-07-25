from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.request import AskRequest, SearchRequest
from app.models.response import AskResponse, HealthResponse, RootResponse, SearchResponse
from app.services import answer_service, health_service, retrieval_service

router = APIRouter()


@router.get(
    "/",
    response_model=RootResponse,
    summary="Service info",
    description="Basic service identity and version.",
)
async def root() -> RootResponse:
    return RootResponse(service="Knowledge Base AI", version="0.1.0")


@router.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Checks embedding model load, ChromaDB connectivity, and Groq API key presence.",
)
async def health() -> HealthResponse:
    return HealthResponse(**health_service.check_health())


@router.post(
    "/api/v1/ask",
    response_model=AskResponse,
    summary="Ask a question",
    description=(
        "Runs retrieval + distance filter + Groq answer. "
        "Returns 200 for both answered and not-found business outcomes. "
        "Returns 500 if GROQ_API_KEY is missing when the LLM would be called."
    ),
)
async def ask(body: AskRequest) -> AskResponse:
    try:
        result = answer_service.ask(body.question)
    except EnvironmentError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AskResponse(**result)


@router.post(
    "/api/v1/search",
    response_model=SearchResponse,
    response_model_exclude_none=True,
    summary="Search chunks",
    description=(
        "Returns top-K retrieved chunks with raw L2 distances. "
        "When DEBUG=True, includes a debug timing/config object."
    ),
)
async def search_endpoint(body: SearchRequest) -> SearchResponse:
    payload = retrieval_service.search_chunks(body.query, top_k=body.top_k)
    return SearchResponse(**payload)
