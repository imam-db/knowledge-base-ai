from __future__ import annotations

import threading
import time

from app.keyword_index import KeywordIndex


class _FakeStore:
    def __init__(self, chunks, version: str = "v1") -> None:
        self.chunks = chunks
        self.version = version
        self.get_all_chunks_calls = 0
        self._lock = threading.Lock()

    def read_version(self) -> str:
        return self.version

    def get_all_chunks(self):
        with self._lock:
            self.get_all_chunks_calls += 1
        time.sleep(0.05)
        return self.chunks


def _chunk(chunk_id: str, text: str) -> dict:
    return {"id": chunk_id, "text": text, "metadata": {"chunk_id": chunk_id}}


def test_snapshot_rebuilds_only_when_version_changes():
    store = _FakeStore([_chunk("a", "alpha beta"), _chunk("b", "gamma delta")])
    index = KeywordIndex(store=store)

    index.search("alpha")
    index.search("gamma")
    assert store.get_all_chunks_calls == 1

    store.version = "v2"
    index.search("alpha")
    assert store.get_all_chunks_calls == 2


def test_version_change_with_same_chunk_count_yields_new_results():
    store = _FakeStore(
        [
            _chunk("a", "alpha beta"),
            _chunk("b", "gamma delta"),
            _chunk("c", "epsilon zeta"),
        ]
    )
    index = KeywordIndex(store=store)
    first = index.search("gamma", top_k=1)
    assert first[0].chunk_id == "b"

    store.chunks = [
        _chunk("d", "gamma delta"),
        _chunk("e", "alpha beta"),
        _chunk("f", "epsilon zeta"),
    ]
    store.version = "v2"
    second = index.search("gamma", top_k=1)

    assert second[0].chunk_id == "d"
    assert store.get_all_chunks_calls == 2


def test_concurrent_search_after_version_change_rebuilds_once():
    store = _FakeStore([_chunk("a", "alpha beta"), _chunk("b", "gamma delta")])
    index = KeywordIndex(store=store)
    index.search("alpha")
    assert store.get_all_chunks_calls == 1

    store.chunks = [
        _chunk("c", "alpha beta"),
        _chunk("d", "gamma delta"),
    ]
    store.version = "v2"

    thread_count = 8
    barrier = threading.Barrier(thread_count)
    results: list[list] = []
    results_lock = threading.Lock()

    def worker() -> None:
        barrier.wait()
        hits = index.search("alpha", top_k=1)
        with results_lock:
            results.append(hits)

    threads = [threading.Thread(target=worker) for _ in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == thread_count
    assert all(hits and hits[0].chunk_id == "c" for hits in results)
    assert store.get_all_chunks_calls == 2
