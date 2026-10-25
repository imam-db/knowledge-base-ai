from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.chroma import ChromaStore


def test_bump_and_read_version(tmp_path: Path) -> None:
    version_path = tmp_path / "nested" / "chroma.version"
    store = ChromaStore(version_path=version_path)

    assert store.read_version() == ""

    store.bump_version()
    first = store.read_version()
    assert first
    assert len(first) == 32
    int(first, 16)

    store.bump_version()
    second = store.read_version()
    assert second
    assert second != first


def test_add_bumps_version_when_collection_delete_raises(tmp_path: Path) -> None:
    version_path = tmp_path / "chroma.version"
    coll = MagicMock()
    coll.delete.side_effect = RuntimeError("delete failed")
    store = ChromaStore(collection=coll, version_path=version_path)

    with pytest.raises(RuntimeError, match="delete failed"):
        store.add(
            document_id="doc-1",
            texts=["hello"],
            embeddings=[[0.1]],
            metadatas=[{"document_id": "doc-1"}],
            ids=["chunk-1"],
        )

    version = store.read_version()
    assert version
    int(version, 16)
    coll.add.assert_not_called()


def test_delete_bumps_version_when_collection_delete_raises(tmp_path: Path) -> None:
    version_path = tmp_path / "chroma.version"
    coll = MagicMock()
    coll.delete.side_effect = RuntimeError("delete failed")
    store = ChromaStore(collection=coll, version_path=version_path)

    with pytest.raises(RuntimeError, match="delete failed"):
        store.delete("doc-1")

    version = store.read_version()
    assert version
    int(version, 16)
