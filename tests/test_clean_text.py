from app.config import load_settings, ROOT_DIR
from app.loaders import clean_text, normalize_page


def test_clean_removes_confidential_and_page_lines():
    settings = load_settings(ROOT_DIR / "config" / "config.yaml")
    raw = "Intro\nConfidential\nBody text\nPage 3\n- 4 -\nMore"
    out = clean_text(raw, settings.cleaning_patterns())
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
