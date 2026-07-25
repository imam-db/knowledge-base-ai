from __future__ import annotations

from collections.abc import Sequence

from sentence_transformers import SentenceTransformer

from app.config import settings

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []
    model = get_model()
    vectors = model.encode(list(texts), show_progress_bar=False, normalize_embeddings=False)
    return [v.tolist() for v in vectors]
