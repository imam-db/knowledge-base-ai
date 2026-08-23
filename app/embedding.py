from __future__ import annotations

from collections.abc import Sequence

from sentence_transformers import SentenceTransformer

from app.core.embeddings import SentenceTransformerEmbedding, get_embedding_provider


def get_model() -> SentenceTransformer:
    """Warm/load the sentence-transformers model (startup + retrieve path)."""
    provider = get_embedding_provider()
    if isinstance(provider, SentenceTransformerEmbedding):
        return provider._get_model()
    # Fallback for unexpected providers: force default adapter load
    return SentenceTransformerEmbedding()._get_model()


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    return get_embedding_provider().embed_documents(texts)
