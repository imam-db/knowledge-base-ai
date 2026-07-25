import uuid

from app.config import make_document_id


def test_document_id_is_stable_uuid5():
    a = make_document_id("sop.pdf")
    b = make_document_id("sop.pdf")
    assert a == b
    assert uuid.UUID(a).version == 5


def test_different_names_different_ids():
    assert make_document_id("a.pdf") != make_document_id("b.pdf")


def test_document_id_uses_basename_only():
    assert make_document_id("/path/to/sop.pdf") == make_document_id("sop.pdf")
