from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from app.chroma import query_similar


def test_query_similar_passes_embedding_and_n_results():
    coll = MagicMock()
    coll.count.return_value = 1
    coll.query.return_value = {
        "ids": [["id-0"]],
        "documents": [["hello"]],
        "metadatas": [[{"document_name": "a.pdf", "page": 1, "chunk_id": 0}]],
        "distances": [[0.25]],
    }
    embedding = [0.1, 0.2, 0.3]

    result = query_similar(embedding, n_results=3, collection=coll)

    coll.query.assert_called_once_with(
        query_embeddings=[[0.1, 0.2, 0.3]],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )
    assert result["documents"][0][0] == "hello"
    assert result["distances"][0][0] == 0.25


def test_query_similar_empty_collection_returns_empty_lists():
    coll = MagicMock()
    coll.count.return_value = 0

    result = query_similar([0.1], n_results=5, collection=coll)

    coll.query.assert_not_called()
    assert result["ids"] == [[]]
    assert result["documents"] == [[]]
    assert result["metadatas"] == [[]]
    assert result["distances"] == [[]]
