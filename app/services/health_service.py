from __future__ import annotations

from app.chroma import get_collection
from app.config import settings
from app.embedding import get_model


def check_health() -> dict[str, str]:
    """Real dependency checks for /health."""
    embedding_status = "error"
    vector_status = "error"
    try:
        model = get_model()
        if model is not None:
            embedding_status = "loaded"
    except Exception:
        embedding_status = "error"

    try:
        coll = get_collection()
        coll.count()
        vector_status = "connected"
    except Exception:
        vector_status = "error"

    groq_status = "configured" if settings.groq_api_key else "missing"

    overall = (
        "healthy"
        if embedding_status == "loaded" and vector_status == "connected"
        else "degraded"
    )
    return {
        "status": overall,
        "embedding": embedding_status,
        "vector_db": vector_status,
        "groq": groq_status,
    }
