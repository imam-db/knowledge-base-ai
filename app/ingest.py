from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import make_document_id, settings
from app.loaders import discover_documents, load_file


class IngestLoadError(Exception):
    """Per-file load/parse failure — fail-soft in the CLI loop."""


def build_chunks_for_documents(
    page_docs: list[Document],
    *,
    document_id: str,
    document_name: str,
    uploaded_at: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[dict[str, Any]]:
    """Split per page Document (inherit page). chunk_id sequential on kept chunks only."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size if chunk_size is not None else settings.chunk_size,
        chunk_overlap=chunk_overlap if chunk_overlap is not None else settings.chunk_overlap,
    )
    split_docs = splitter.split_documents(page_docs)

    chunks: list[dict[str, Any]] = []
    chunk_id = 0
    for doc in split_docs:
        text = (doc.page_content or "").strip()
        if not text:
            continue
        meta = {
            "document_id": document_id,
            "document_name": document_name,
            "page": int(doc.metadata.get("page", 1)),
            "chunk_id": chunk_id,
            "uploaded_at": uploaded_at,
        }
        chunks.append({"text": text, "metadata": meta, "id": f"{document_id}_{chunk_id}"})
        chunk_id += 1
    return chunks


def ingest_file(path: Path) -> tuple[int, dict[str, Any] | None]:
    """Returns (chunk_count, sample_chunk_or_none).

    Load/parse errors raise IngestLoadError (fail-soft).
    Embedding/Chroma errors propagate (fatal — abort pipeline).
    """
    document_name = path.name
    document_id = make_document_id(document_name)
    uploaded_at = date.today().isoformat()

    try:
        page_docs = load_file(path)
    except Exception as exc:
        raise IngestLoadError(str(exc)) from exc

    if not page_docs:
        print(f"WARNING: skipping empty document after load/clean: {document_name}")
        # Spec: empty after clean → skip with warning; prior vectors NOT deleted
        return 0, None

    chunks = build_chunks_for_documents(
        page_docs,
        document_id=document_id,
        document_name=document_name,
        uploaded_at=uploaded_at,
    )
    if not chunks:
        print(f"WARNING: skipping document with no chunks: {document_name}")
        return 0, None

    from app.chroma import replace_document_chunks
    from app.embedding import embed_texts

    texts = [c["text"] for c in chunks]
    # Fatal on failure (do not catch): embedding + chroma
    embeddings = embed_texts(texts)
    metadatas = [c["metadata"] for c in chunks]
    ids = [c["id"] for c in chunks]

    replace_document_chunks(
        document_id=document_id,
        texts=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )
    return len(chunks), chunks[0]


def run_ingest() -> int:
    docs_dir = settings.documents_dir
    if not docs_dir.exists():
        print(f"ERROR: documents directory not found: {docs_dir}")
        return 1

    files = discover_documents(docs_dir)
    if not files:
        print(f"ERROR: no PDF/DOCX files in {docs_dir}")
        return 1

    processed = 0
    total_chunks = 0
    sample: dict[str, Any] | None = None

    for path in files:
        try:
            n, first = ingest_file(path)
        except IngestLoadError as exc:
            print(f"ERROR: failed to load {path.name}: {exc}")
            continue
        # Embedding/Chroma exceptions are not caught — abort with traceback
        if n <= 0:
            continue
        processed += 1
        total_chunks += n
        if sample is None and first is not None:
            sample = first

    from app.keyword_index import reset_keyword_index

    reset_keyword_index()

    print("Ingestion complete")
    print(f"- Documents processed: {processed}")
    print(f"- Chunks created: {total_chunks}")
    if sample is None:
        print("- Sample chunk: (none — no chunks indexed)")
        return 1 if processed == 0 else 0

    text_preview = sample["text"][:200]
    if len(sample["text"]) > 200:
        text_preview += "..."
    print("- Sample chunk:")
    print(f'  text: "{text_preview}"')
    print(f"  metadata: {sample['metadata']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_ingest())
