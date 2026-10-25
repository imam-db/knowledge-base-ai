from __future__ import annotations

import io
import uuid
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import chromadb
import pytest
from fastapi.testclient import TestClient
from langchain_core.documents import Document

from app import keyword_index as keyword_index_module
from app.config import make_document_id, settings
from app.core import chroma as core_chroma
from app.core.chroma import ChromaStore
from app.keyword_index import KeywordIndex, get_keyword_index
from app.loaders import SUPPORTED_SUFFIXES
from app.services.ingestion_service import assert_content_matches_extension

with (
    patch("app.main.get_model"),
    patch("app.main.get_collection"),
):
    from app.main import app

client = TestClient(app)


def _fake_embed(texts):
    """Deterministic fixed-length vectors; keyword search never depends on them."""
    vectors = []
    for text in texts:
        seed = sum((index + 1) * ord(char) for index, char in enumerate(text)) % 97
        vectors.append([float((seed + offset) % 11) / 10.0 for offset in range(8)])
    return vectors


def _add_chunks(
    store: ChromaStore,
    *,
    document_id: str,
    texts: list[str],
    ids: list[str],
    document_name: str | None = None,
) -> None:
    metadatas = [
        {
            "document_id": document_id,
            "document_name": document_name or f"{document_id}.pdf",
            "page": 1,
            "chunk_id": index,
            "uploaded_at": "2026-01-01",
        }
        for index in range(len(texts))
    ]
    store.add(
        document_id=document_id,
        texts=texts,
        embeddings=_fake_embed(texts),
        metadatas=metadatas,
        ids=ids,
    )


def _upload_file(term: str) -> tuple[str, bytes]:
    """Build a file accepted by the real upload validation, preferring text suffixes."""
    suffix = next(
        (
            candidate
            for candidate in (".md", ".txt", ".pdf", ".docx")
            if candidate in SUPPORTED_SUFFIXES
        ),
        None,
    )
    if suffix is None:
        raise AssertionError(f"No usable upload suffix in {SUPPORTED_SUFFIXES!r}")

    name = f"regression-{uuid.uuid4().hex[:8]}{suffix}"
    if suffix == ".pdf":
        content = b"%PDF-1.4\n% " + term.encode("utf-8") + b"\n"
    elif suffix == ".docx":
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("word/document.xml", f"<w:document>{term}</w:document>")
        content = buffer.getvalue()
    else:
        content = f"{term}\n".encode("utf-8")

    assert_content_matches_extension(name, content)
    return name, content


def _upload_term(env: SimpleNamespace, term: str) -> dict:
    filename, content = _upload_file(term)
    env.loaded_docs[:] = [
        Document(
            page_content=f"Synthetic document body containing {term} for regression coverage.",
            metadata={
                "page": 1,
                "source": str(env.docs_dir / filename),
                "document_name": filename,
            },
        )
    ]
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": (filename, content, "application/octet-stream")},
        headers={"X-API-Key": "test-key"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["document_id"] == make_document_id(filename)
    assert body["chunks_created"] >= 1
    return body


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    monkeypatch.setattr(settings, "documents_dir", docs_dir)
    monkeypatch.setattr(settings, "admin_api_key", "test-key")

    chroma_client = chromadb.EphemeralClient()
    collection = chroma_client.create_collection(
        name=f"kw-regression-{uuid.uuid4().hex}"
    )
    store = ChromaStore(
        collection=collection,
        version_path=tmp_path / "chroma.version",
    )

    # App helpers resolve these module globals at call time.
    monkeypatch.setattr(core_chroma, "_default_store", store)
    index = KeywordIndex(store=store)
    monkeypatch.setattr(keyword_index_module, "_default_index", index)

    loaded_docs: list[Document] = []
    monkeypatch.setattr("app.ingest.load_file", lambda _path: list(loaded_docs))
    monkeypatch.setattr("app.embedding.embed_texts", _fake_embed)

    return SimpleNamespace(
        store=store,
        index=index,
        collection=collection,
        docs_dir=docs_dir,
        loaded_docs=loaded_docs,
    )


def test_upload_invalidates_primed_keyword_index(env: SimpleNamespace) -> None:
    _add_chunks(
        env.store,
        document_id="prime-doc",
        texts=[
            "Baseline policy about annual leave and approvals.",
            "Baseline guidance for requesting leave through the portal.",
        ],
        ids=["prime-doc_0", "prime-doc_1"],
    )
    primed = get_keyword_index().search("annual", top_k=1)
    assert primed and "annual" in primed[0].text

    term = "zorblaxquota"
    _upload_term(env, term)

    hits = get_keyword_index().search(term)
    assert hits
    assert term in hits[0].text


def test_delete_removes_uploaded_term_from_keyword_search(env: SimpleNamespace) -> None:
    term = "obsoletezorbterm"
    uploaded = _upload_term(env, term)
    assert any(term in hit.text for hit in get_keyword_index().search(term))

    response = client.delete(
        f"/api/v1/documents/{uploaded['document_id']}",
        headers={"X-API-Key": "test-key"},
    )
    assert response.status_code == 200, response.text

    hits = get_keyword_index().search(term)
    assert not any(term in hit.text for hit in hits)


def test_same_chunk_count_different_ids_and_terms(env: SimpleNamespace) -> None:
    term_a = "alphacohortterm"
    term_b = "betacohortterm"

    _add_chunks(
        env.store,
        document_id="doc-a",
        texts=[f"{term_a} belongs to document A.", "shared filler for document A."],
        ids=["doc-a_0", "doc-a_1"],
    )
    first_hits = get_keyword_index().search(term_a)
    assert any(term_a in hit.text for hit in first_hits)

    env.store.delete("doc-a")
    _add_chunks(
        env.store,
        document_id="doc-b",
        texts=[f"{term_b} belongs to document B.", "shared filler for document B."],
        ids=["doc-b_0", "doc-b_1"],
    )
    assert env.collection.count() == 2

    hits_b = get_keyword_index().search(term_b)
    matching_b = [hit for hit in hits_b if term_b in hit.text]
    assert matching_b
    assert matching_b[0].chunk_id == "doc-b_0"

    hits_a = get_keyword_index().search(term_a)
    assert not any(term_a in hit.text for hit in hits_a)


def test_second_store_sharing_version_path_invalidates_first_index(
    env: SimpleNamespace,
) -> None:
    index = get_keyword_index()
    assert index.search("warmup") == []

    version_before = env.store.read_version()
    second_store = ChromaStore(
        collection=env.collection,
        version_path=env.store.version_path,
    )
    assert second_store.version_path == env.store.version_path

    term = "crossprocesszorbterm"
    _add_chunks(
        second_store,
        document_id="cli-doc",
        texts=[f"{term} was written by the separate store instance."],
        ids=["cli-doc_0"],
    )

    assert second_store.read_version() != version_before
    assert env.store.read_version() == second_store.read_version()

    hits = index.search(term)
    assert hits
    assert term in hits[0].text
    assert hits[0].chunk_id == "cli-doc_0"
