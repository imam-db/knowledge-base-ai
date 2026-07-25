from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.documents_service import get_stats, list_documents


def test_get_stats_counts_unique_documents_and_chunks():
    coll = MagicMock()
    coll.count.return_value = 3
    metadatas = [
        {"document_name": "a.pdf", "page": 1},
        {"document_name": "a.pdf", "page": 2},
        {"document_name": "b.pdf", "page": 1},
    ]
    with (
        patch("app.services.documents_service.get_collection", return_value=coll),
        patch("app.services.documents_service.get_all_metadatas", return_value=metadatas),
    ):
        assert get_stats() == {"documents": 2, "chunks": 3}


def test_list_documents_groups_max_page_and_uploaded_at():
    metadatas = [
        {"document_name": "SOP.pdf", "page": 1, "uploaded_at": "2026-07-25"},
        {"document_name": "SOP.pdf", "page": 4, "uploaded_at": "2026-07-25"},
        {"document_name": "FAQ.docx", "page": 1, "uploaded_at": "2026-07-24"},
    ]
    with patch("app.services.documents_service.get_all_metadatas", return_value=metadatas):
        result = list_documents()
    assert result["documents"] == [
        {"name": "FAQ.docx", "pages": 1, "uploaded_at": "2026-07-24"},
        {"name": "SOP.pdf", "pages": 4, "uploaded_at": "2026-07-25"},
    ]
