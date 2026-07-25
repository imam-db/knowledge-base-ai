# Milestone 1: Ingestion Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local document ingestion pipeline that loads PDF/DOCX from `documents/`, cleans and chunks text, embeds with sentence-transformers, and persists to ChromaDB with replace-by-`document_id` semantics.

**Architecture:** Thin modules under `app/` — `config`, `loaders`, `embedding`, `chroma` — orchestrated by runnable `ingest.py`. LangChain is used only for loaders and `RecursiveCharacterTextSplitter`. Embedding and Chroma use native APIs. Re-ingest replaces prior chunks for the same UUID5 `document_id`.

**Tech Stack:** Python 3.10+, langchain / langchain-community (loaders + splitter only), sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`), chromadb PersistentClient, python-dotenv, pytest (unit tests for pure helpers).

**Spec:** `docs/superpowers/specs/2026-07-25-ingestion-engine-design.md`

---

## File map

| Path | Responsibility |
|------|----------------|
| `requirements.txt` | Pinned-enough deps for M1 |
| `.env` | Runtime overrides (paths, chunk size, model) |
| `.env.example` | Same keys without secrets (optional but useful) |
| `app/__init__.py` | Package marker |
| `app/config.py` | Settings from env + defaults + cleaning patterns |
| `app/loaders.py` | Flat scan, load PDF/DOCX, clean text, normalize page |
| `app/embedding.py` | Lazy sentence-transformers wrapper |
| `app/chroma.py` | PersistentClient, delete-by-document_id, add |
| `app/ingest.py` | Pipeline + CLI + summary |
| `app/main.py` | Stub placeholder |
| `documents/.gitkeep` | Keep empty folder in git |
| `tests/test_clean_text.py` | Cleaning + sequential chunk_id helpers |
| `tests/test_document_id.py` | UUID5 stability |

---

### Task 1: Project scaffolding & dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `documents/.gitkeep`
- Create: `.gitignore`

- [ ] **Step 1: Create `.gitignore`**

```gitignore
__pycache__/
*.py[cod]
.venv/
venv/
.env
chroma_db/
.pytest_cache/
*.egg-info/
dist/
build/
```

- [ ] **Step 2: Create `requirements.txt`**

```text
langchain>=0.3.0
langchain-community>=0.3.0
langchain-text-splitters>=0.3.0
pypdf>=4.0.0
docx2txt>=0.8
sentence-transformers>=3.0.0
chromadb>=0.5.0
python-dotenv>=1.0.0
pytest>=8.0.0
```

Note: If `RecursiveCharacterTextSplitter` import path is `langchain_text_splitters` in installed versions, prefer that import in code (Task 3). Keep `langchain` / `langchain-community` for loaders.

- [ ] **Step 3: Create `.env` and `.env.example`**

```env
DOCUMENTS_DIR=./documents
CHROMA_DIR=./chroma_db
CHROMA_COLLECTION=knowledge_base
CHUNK_SIZE=700
CHUNK_OVERLAP=100
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
COMPANY_HEADER=
```

- [ ] **Step 4: Create stub files**

`app/__init__.py` — empty.

`app/main.py`:

```python
"""Application entry point — wired in Milestone 4/5 (API)."""
```

`documents/.gitkeep` — empty file.

- [ ] **Step 5: Create venv and install**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Expected: install succeeds (sentence-transformers may take a few minutes).

- [ ] **Step 6: Commit**

```powershell
git add .gitignore requirements.txt .env.example app/__init__.py app/main.py documents/.gitkeep
git commit -m "Scaffold M1 project layout and dependencies"
```

Do **not** commit `.env` (gitignored). `.env.example` is fine.

---

### Task 2: `config.py` + document_id helper tests (TDD)

**Files:**
- Create: `app/config.py`
- Create: `tests/test_document_id.py`
- Create: `tests/conftest.py` (optional path bootstrap)

- [ ] **Step 1: Write failing tests for UUID5 document_id**

Create `tests/test_document_id.py`:

```python
import uuid

from app.config import make_document_id


def test_document_id_is_stable_uuid5():
    a = make_document_id("sop.pdf")
    b = make_document_id("sop.pdf")
    assert a == b
    assert uuid.UUID(a).version == 5


def test_different_names_different_ids():
    assert make_document_id("a.pdf") != make_document_id("b.pdf")
```

Create `tests/conftest.py` so `app` is importable when running from repo root:

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

- [ ] **Step 2: Run tests — expect fail**

```powershell
pytest tests/test_document_id.py -v
```

Expected: FAIL (`ModuleNotFoundError` or missing `make_document_id`).

- [ ] **Step 3: Implement `app/config.py`**

```python
from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root = parent of app/
ROOT_DIR = Path(__file__).resolve().parents[1]


def _path_from_env(key: str, default: str) -> Path:
    raw = os.getenv(key, default)
    p = Path(raw)
    return p if p.is_absolute() else (ROOT_DIR / p).resolve()


@dataclass
class Settings:
    documents_dir: Path = field(default_factory=lambda: _path_from_env("DOCUMENTS_DIR", "./documents"))
    chroma_dir: Path = field(default_factory=lambda: _path_from_env("CHROMA_DIR", "./chroma_db"))
    chroma_collection: str = field(default_factory=lambda: os.getenv("CHROMA_COLLECTION", "knowledge_base"))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "700")))
    chunk_overlap: int = field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "100")))
    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
        )
    )
    # Optional company header token; empty = still match Confidential / page numbers
    company_header: str = field(default_factory=lambda: os.getenv("COMPANY_HEADER", "").strip())

    def cleaning_patterns(self) -> list[re.Pattern[str]]:
        patterns: list[str] = [
            r"(?i)^\s*confidential\s*$",
            r"(?i)^\s*page\s+\d+\s*$",
            r"^\s*-?\s*\d+\s*-?\s*$",
        ]
        if self.company_header:
            escaped = re.escape(self.company_header)
            patterns.insert(0, rf"(?i)^\s*{escaped}\s*$")
        return [re.compile(p) for p in patterns]


settings = Settings()


def make_document_id(document_name: str) -> str:
    """Stable UUID5 from basename for replace-by-document_id."""
    name = Path(document_name).name
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))
```

- [ ] **Step 4: Run tests — expect pass**

```powershell
pytest tests/test_document_id.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add app/config.py tests/test_document_id.py tests/conftest.py
git commit -m "Add config settings and stable document_id helper"
```

---

### Task 3: Text cleaning (TDD) + `loaders.py`

**Files:**
- Create: `tests/test_clean_text.py`
- Create: `app/loaders.py`

- [ ] **Step 1: Write failing cleaning tests**

```python
from app.config import Settings
from app.loaders import clean_text, normalize_page


def test_clean_removes_confidential_and_page_lines():
    raw = "Intro\nConfidential\nBody text\nPage 3\n- 4 -\nMore"
    out = clean_text(raw, Settings().cleaning_patterns())
    assert "Confidential" not in out
    assert "Page 3" not in out
    assert "Intro" in out
    assert "Body text" in out
    assert "More" in out


def test_normalize_page_pdf_zero_based():
    assert normalize_page(0, has_page_metadata=True) == 1
    assert normalize_page(7, has_page_metadata=True) == 8


def test_normalize_page_docx_default():
    assert normalize_page(None, has_page_metadata=False) == 1
```

- [ ] **Step 2: Run tests — expect fail**

```powershell
pytest tests/test_clean_text.py -v
```

Expected: FAIL (import / missing functions).

- [ ] **Step 3: Implement `app/loaders.py`**

```python
from __future__ import annotations

import re
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_core.documents import Document

from app.config import Settings, settings

SUPPORTED_SUFFIXES = {".pdf", ".docx"}


def clean_text(text: str, patterns: list[re.Pattern[str]]) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if any(p.match(line.strip()) for p in patterns):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def normalize_page(raw_page: int | None, *, has_page_metadata: bool) -> int:
    """Store 1-based pages. DOCX / missing metadata always returns 1."""
    if not has_page_metadata or raw_page is None:
        return 1
    # PyPDFLoader uses 0-based page in metadata
    return int(raw_page) + 1


def discover_documents(directory: Path | None = None) -> list[Path]:
    directory = directory or settings.documents_dir
    if not directory.exists():
        return []
    files = [
        p
        for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    ]
    return sorted(files, key=lambda p: p.name.lower())


def load_file(path: Path, cfg: Settings | None = None) -> list[Document]:
    """Load one file into per-page/segment Documents with cleaned text and normalized page."""
    cfg = cfg or settings
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raw_docs = PyPDFLoader(str(path)).load()
        has_page = True
    elif suffix == ".docx":
        raw_docs = Docx2txtLoader(str(path)).load()
        has_page = False
    else:
        raise ValueError(f"Unsupported file type: {path}")

    patterns = cfg.cleaning_patterns()
    out: list[Document] = []
    for doc in raw_docs:
        page_raw = doc.metadata.get("page") if has_page else None
        page = normalize_page(page_raw if isinstance(page_raw, int) else None, has_page_metadata=has_page)
        text = clean_text(doc.page_content or "", patterns)
        if not text:
            continue
        out.append(
            Document(
                page_content=text,
                metadata={
                    "page": page,
                    "source": str(path),
                    "document_name": path.name,
                },
            )
        )
    return out
```

- [ ] **Step 4: Run cleaning tests — expect pass**

```powershell
pytest tests/test_clean_text.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```powershell
git add app/loaders.py tests/test_clean_text.py
git commit -m "Add document loaders and configurable text cleaning"
```

---

### Task 4: `embedding.py` + `chroma.py`

**Files:**
- Create: `app/embedding.py`
- Create: `app/chroma.py`

- [ ] **Step 1: Implement `app/embedding.py`**

```python
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
```

- [ ] **Step 2: Implement `app/chroma.py`**

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.config import settings


def get_collection(name: str | None = None) -> Collection:
    client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    return client.get_or_create_collection(name=name or settings.chroma_collection)


def replace_document_chunks(
    *,
    document_id: str,
    texts: Sequence[str],
    embeddings: Sequence[Sequence[float]],
    metadatas: Sequence[dict[str, Any]],
    ids: Sequence[str],
    collection: Collection | None = None,
) -> None:
    coll = collection or get_collection()
    coll.delete(where={"document_id": document_id})
    if not texts:
        return
    coll.add(
        documents=list(texts),
        embeddings=list(embeddings),
        metadatas=list(metadatas),
        ids=list(ids),
    )
```

Chroma metadata values must be str/int/float/bool — our fields already are (`document_id` str, `document_name` str, `page` int, `chunk_id` int, `uploaded_at` str).

- [ ] **Step 3: Smoke-import check**

```powershell
python -c "from app.embedding import embed_texts; from app.chroma import get_collection; print('ok')"
```

Expected: prints `ok` (may download model weights on first real encode later).

- [ ] **Step 4: Commit**

```powershell
git add app/embedding.py app/chroma.py
git commit -m "Add local embeddings and Chroma persistence helpers"
```

---

### Task 5: `ingest.py` pipeline + CLI

**Files:**
- Create: `app/ingest.py`
- Create: `tests/test_chunk_metadata.py`

- [ ] **Step 1: Write test for sequential chunk_id (kept chunks only)**

```python
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
```

- [ ] **Step 2: Run test — expect fail**

```powershell
pytest tests/test_chunk_metadata.py -v
```

Expected: FAIL

- [ ] **Step 3: Implement `app/ingest.py`**

Paste this file **as-is** (`sys.path` bootstrap is at the top, before `app` imports):

```python
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

from app.chroma import replace_document_chunks
from app.config import make_document_id, settings
from app.embedding import embed_texts
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
```

- [ ] **Step 4: Run unit tests**

```powershell
pytest tests/ -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```powershell
git add app/ingest.py tests/test_chunk_metadata.py
git commit -m "Add ingest pipeline CLI with per-page chunk metadata"
```

---

### Task 6: End-to-end manual verification

**Files:**
- Create: sample file under `documents/` (user-provided or a tiny generated PDF for smoke test)

- [ ] **Step 1: Add a sample document to `documents/`**

Prefer copying a real SOP PDF/DOCX. If none exists, create a minimal DOCX smoke file (do not commit binaries unless user asks):

```powershell
python -c "import zipfile; from pathlib import Path; p=Path('documents/sample_faq.docx'); body='Confidential\n\nFAQ: Cara reset password adalah hubungi IT Support.\nPage 1\n\nKebijakan cuti: ajukan via portal HR.'; content_types='<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/></Types>'; rels='<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/></Relationships>'; doc='<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"><w:body><w:p><w:r><w:t>'+body+'</w:t></w:r></w:p></w:body></w:document>';
zf=zipfile.ZipFile(p,'w'); zf.writestr('[Content_Types].xml', content_types); zf.writestr('_rels/.rels', rels); zf.writestr('word/document.xml', doc); zf.close(); print('wrote', p)"
```

- [ ] **Step 2: Run ingest**

```powershell
python app/ingest.py
```

Expected output shape:

```text
Ingestion complete
- Documents processed: N
- Chunks created: M
- Sample chunk:
  text: "..."
  metadata: {'document_id': '...', 'document_name': '...', 'page': ..., 'chunk_id': 0, 'uploaded_at': 'YYYY-MM-DD'}
```

- [ ] **Step 3: Run ingest again (replace check)**

```powershell
python app/ingest.py
```

Expected: same `Documents processed` / similar chunk count (not doubled). Optionally verify collection count:

```powershell
python -c "from app.chroma import get_collection; c=get_collection(); print(c.count())"
```

Run twice; count should stay stable for unchanged files.

- [ ] **Step 4: Commit any remaining non-binary scaffolding** (skip committing sample PDFs unless requested)

```powershell
git status
git add -u
git commit -m "Complete M1 ingest verification scaffolding"
```

Only commit if there are meaningful code/doc changes left.

---

## Spec coverage checklist

| Spec requirement | Task |
|------------------|------|
| Flat scan PDF/DOCX | Task 3 |
| Configurable cleaning | Task 2–3 |
| Split per page, inherit `page` | Task 5 |
| PDF 1-based page | Task 3 |
| DOCX `page=1` | Task 3 |
| UUID5 `document_id` | Task 2 |
| Sequential `chunk_id` (no gaps) | Task 5 |
| sentence-transformers local embed | Task 4 |
| Chroma PersistentClient `knowledge_base` | Task 4 |
| Replace by `document_id` | Task 4–5 |
| Empty doc after clean: warn, no delete | Task 5 |
| Fail-soft per file | Task 5 |
| CLI summary + sample | Task 5 |
| `main.py` stub | Task 1 |
| No retrieval/LLM/API | All tasks |

---

## Execution notes

- Working directory: repo root `rag/`.
- First embedding run downloads the MiniLM model — needs network once.
- Do not implement retrieval, Groq, or FastAPI in this plan.
- Orphan prune (file deleted from disk) is explicitly out of scope for M1.
