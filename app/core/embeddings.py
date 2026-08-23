from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from sentence_transformers import SentenceTransformer

from app.config import settings


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed one or more document texts."""

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""


class SentenceTransformerEmbedding:
    """sentence-transformers adapter using the configured model name."""

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(settings.embedding_model)
        return self._model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._get_model().encode(
            list(texts), show_progress_bar=False, normalize_embeddings=False
        )
        result: list[list[float]] = []
        for v in vectors:
            result.append(v.tolist() if hasattr(v, "tolist") else list(v))
        return result

    def embed_query(self, text: str) -> list[float]:
        vectors = self.embed_documents([text])
        return vectors[0] if vectors else []


_default_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _default_provider
    if _default_provider is None:
        _default_provider = SentenceTransformerEmbedding()
    return _default_provider
