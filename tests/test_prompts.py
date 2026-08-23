from __future__ import annotations

from app.prompts import build_prompt, get_guardrail_message, get_system_instructions


def test_system_prompt_is_neutral_indonesian():
    text = get_system_instructions()
    assert "knowledge application" in text.lower()
    assert "perusahaan" not in text.lower()
    assert "HR" not in text
    assert "Konteks:" not in text


def test_guardrail_message_loaded_from_file():
    guardrail = get_guardrail_message()
    assert guardrail == "Maaf, informasi tersebut tidak ditemukan dalam dokumen yang tersedia."


def test_build_prompt_uses_system_file_content():
    from app.retrieve import SearchResult

    chunk = SearchResult(
        rank=1,
        document_name="doc.pdf",
        page=1,
        chunk_id=0,
        distance=1.0,
        text="Isi dokumen.",
    )
    prompt = build_prompt("Apa isinya?", [chunk])
    assert get_system_instructions() in prompt
    assert "Isi dokumen." in prompt
    assert "Apa isinya?" in prompt
