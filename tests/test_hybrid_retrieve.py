from __future__ import annotations

from app.keyword_index import KeywordIndex, tokenize
from app.retrieve import reciprocal_rank_fusion


def test_tokenize_lowercases_words():
    tokens = tokenize("Owners' Charter Winter Transfer")
    assert "charter" in tokens
    assert "winter" in tokens
    assert "transfer" in tokens

class _FakeStore:
    def __init__(self, chunks):
        self._chunks = chunks

    def read_version(self):
        return "v1"

    def get_all_chunks(self):
        return self._chunks


def test_bm25_prefers_exact_phrase_chunk():
    chunks = [
        {
            "id": "a",
            "text": "Premier League 2 development phase games programme",
            "metadata": {"document_name": "plhandbook.pdf", "page": 254, "chunk_id": 0},
        },
        {
            "id": "b",
            "text": "Subject to Rules C.18, each Club shall play two League Matches against every other Club",
            "metadata": {"document_name": "plhandbook.pdf", "page": 63, "chunk_id": 1},
        },
    ]
    index = KeywordIndex(store=_FakeStore(chunks))
    hits = index.search("each Club shall play League Matches", top_k=2)
    assert hits
    assert hits[0].chunk_id == "b"
    assert hits[0].metadata["page"] == 63


def test_reciprocal_rank_fusion_promotes_shared_ids():
    fused = reciprocal_rank_fusion(
        [
            ["sem-a", "sem-b", "sem-c"],
            ["kw-b", "sem-a", "kw-d"],
        ],
        rrf_k=60,
    )
    assert fused[0][0] == "sem-a"
