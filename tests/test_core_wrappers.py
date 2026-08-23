from __future__ import annotations

from unittest.mock import MagicMock

from app.core.chroma import ChromaStore
from app.core.embeddings import SentenceTransformerEmbedding


def test_embedding_provider_embed_query_uses_documents_path():
    provider = SentenceTransformerEmbedding()
    provider._model = MagicMock()
    provider._model.encode.return_value = [[0.1, 0.2]]

    vector = provider.embed_query("hello")
    assert vector == [0.1, 0.2]
    provider._model.encode.assert_called_once()


def test_chroma_store_search_empty_collection():
    coll = MagicMock()
    coll.count.return_value = 0
    store = ChromaStore(collection=coll)
    result = store.search([0.1], n_results=3)
    assert result == {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    coll.query.assert_not_called()


def test_chroma_store_add_replaces_then_adds():
    coll = MagicMock()
    store = ChromaStore(collection=coll)
    store.add(
        document_id="doc-1",
        texts=["a"],
        embeddings=[[0.1]],
        metadatas=[{"document_id": "doc-1"}],
        ids=["id-1"],
    )
    coll.delete.assert_called_once_with(where={"document_id": "doc-1"})
    coll.add.assert_called_once()


def test_chroma_store_delete_and_list():
    coll = MagicMock()
    coll.count.return_value = 1
    coll.get.return_value = {"metadatas": [{"document_name": "a.pdf"}]}
    store = ChromaStore(collection=coll)

    store.delete("doc-1")
    coll.delete.assert_called_once_with(where={"document_id": "doc-1"})

    metas = store.list_documents()
    assert metas == [{"document_name": "a.pdf"}]
