from langchain_core.documents import Document

from app.ingest import build_chunks_for_documents


def test_chunk_ids_are_sequential_without_gaps():
    pages = [
        Document(page_content="A" * 50, metadata={"page": 1, "document_name": "a.pdf"}),
        Document(page_content="   ", metadata={"page": 2, "document_name": "a.pdf"}),
        Document(page_content="B" * 50, metadata={"page": 3, "document_name": "a.pdf"}),
    ]
    chunks = build_chunks_for_documents(
        pages,
        document_id="id-1",
        document_name="a.pdf",
        uploaded_at="2026-07-25",
        chunk_size=40,
        chunk_overlap=0,
    )
    ids = [c["metadata"]["chunk_id"] for c in chunks]
    assert ids == list(range(len(ids)))
    assert all(c["metadata"]["page"] in (1, 3) for c in chunks)
