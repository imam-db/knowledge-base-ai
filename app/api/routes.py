from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import require_admin_api_key
from app.models.request import AskRequest, SearchRequest
from app.models.response import (
    AskResponse,
    DeleteResponse,
    DocumentsResponse,
    HealthResponse,
    RootResponse,
    SearchResponse,
    StatsResponse,
    UploadResponse,
)
from app.services import answer_service, documents_service, health_service, ingestion_service, retrieval_service
from app.services.documents_service import DocumentDeleteError, DocumentNotFoundError
from app.services.ingestion_service import UploadValidationError

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


@router.get(
    "/api/v1/stats",
    response_model=StatsResponse,
    summary="Index stats",
    description="Returns unique document count and total chunk count from ChromaDB.",
)
async def stats() -> StatsResponse:
    return StatsResponse(**documents_service.get_stats())


@router.get(
    "/api/v1/documents",
    response_model=DocumentsResponse,
    summary="List indexed documents",
    description=(
        "Lists documents grouped from chunk metadata: max page as page count "
        "and uploaded_at from any chunk of that document."
    ),
)
async def documents() -> DocumentsResponse:
    return DocumentsResponse(**documents_service.list_documents())


@router.post(
    "/api/v1/documents/upload",
    response_model=UploadResponse,
    summary="Upload and ingest a document",
    description=(
        "Accepts a single .pdf or .docx (max 20MB), saves it under documents/, "
        "and runs sync ingestion for that file only. Requires X-API-Key. "
        "Same filename replaces the previous document (UUID5 document_id)."
    ),
)
async def upload_document(
    file: UploadFile = File(...),
    _: None = Depends(require_admin_api_key),
) -> UploadResponse:
    content = await file.read()
    try:
        result = ingestion_service.ingest_uploaded_file(
            filename=file.filename or "",
            content=content,
        )
    except UploadValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UploadResponse(**result)


@router.delete(
    "/api/v1/documents/{document_id}",
    response_model=DeleteResponse,
    summary="Delete an indexed document",
    description=(
        "Deletes all Chroma chunks for document_id, then removes the file under "
        "documents/ if present. Requires X-API-Key."
    ),
)
async def delete_document(
    document_id: str,
    _: None = Depends(require_admin_api_key),
) -> DeleteResponse:
    try:
        result = documents_service.delete_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentDeleteError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return DeleteResponse(**result)


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
