from __future__ import annotations

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.api.deps import require_admin_api_key
from app.models.request import AskRequest, SearchRequest
from app.models.response import (
    AboutResponse,
    AskResponse,
    DeleteResponse,
    DocumentsResponse,
    EvalSnapshot,
    HealthResponse,
    PipelineStep,
    AboutLiveStats,
    RootResponse,
    SearchResponse,
    StatsResponse,
    UiConfigResponse,
    UploadResponse,
)
from app.services import answer_service, documents_service, health_service, ingestion_service, retrieval_service
from app.services.documents_service import DocumentDeleteError, DocumentNotFoundError
from app.services.ingestion_service import UploadValidationError
from app.config import settings

router = APIRouter()


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

@router.get(
    "/",
    response_model=RootResponse,
    summary="Service info",
    description="Basic service identity and version.",
)
async def root() -> RootResponse:
    return RootResponse(service=settings.app_name, version="0.1.0")


@router.get(
    "/api/v1/config",
    response_model=UiConfigResponse,
    summary="Public UI config",
    description="Frontend-facing UI mode and copy (portfolio vs playground).",
)
async def ui_config() -> UiConfigResponse:
    ui = settings.ui
    return UiConfigResponse(
        app_name=settings.app_name,
        mode=ui.mode,  # type: ignore[arg-type]
        show_documents=ui.show_documents,
        show_about=ui.show_about,
        back_link=ui.back_link,
        back_label=ui.back_label,
        subtitle=ui.subtitle,
        empty_state_title=ui.empty_state_title,
        empty_state_description=ui.empty_state_description,
        example_questions=ui.example_questions,
    )


@router.get(
    "/api/v1/about",
    response_model=AboutResponse,
    summary="Portfolio about / case study",
    description="Narrative case study plus live index stats (portfolio mode).",
)
async def about() -> AboutResponse:
    if not settings.ui.show_about or settings.about is None:
        return AboutResponse(show=False)

    about_cfg = settings.about
    index_stats = documents_service.get_stats()
    eval_snapshot: EvalSnapshot | None = None
    if about_cfg.eval is not None:
        ev = about_cfg.eval
        eval_snapshot = EvalSnapshot(
            dataset=ev.dataset,
            questions=ev.questions,
            hit_at_5=ev.hit_at_5,
            mrr=ev.mrr,
            unanswerable_empty_rate=ev.unanswerable_empty_rate,
            note=ev.note or None,
        )

    return AboutResponse(
        show=True,
        title=about_cfg.title,
        tagline=about_cfg.tagline,
        problem=about_cfg.problem,
        approach=about_cfg.approach,
        pipeline=[
            PipelineStep(label=step.label, detail=step.detail)
            for step in about_cfg.pipeline
        ],
        guardrails=about_cfg.guardrails,
        tradeoffs=about_cfg.tradeoffs,
        eval=eval_snapshot,
        stats=AboutLiveStats(
            documents=index_stats["documents"],
            chunks=index_stats["chunks"],
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            embedding_model=settings.embedding_model,
            llm_model=settings.groq_model,
            hybrid_enabled=settings.retrieval.hybrid.enabled,
            top_k=settings.retrieval.top_k,
        ),
    )


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
    "/api/v1/ask/stream",
    summary="Ask a question (SSE stream)",
    description=(
        "Streams retrieval status, sources, answer tokens, then a done payload. "
        "Events: status, sources, token, done, error."
    ),
)
async def ask_stream(body: AskRequest) -> StreamingResponse:
    def event_gen() -> Iterator[str]:
        try:
            for item in answer_service.ask_events(body.question):
                yield _sse(str(item["event"]), dict(item["data"]))
        except Exception as exc:
            yield _sse("error", {"detail": str(exc)})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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
